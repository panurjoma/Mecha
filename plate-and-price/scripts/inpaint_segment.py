"""Remove unwanted objects from one moment of a recording and fill the background in (video inpainting, local GPU).

Run with the Python of the inpainting environment (PyTorch + ultralytics SAM2 + ProPainter, see below), not with `uv run`:

    <tools>/venv/Scripts/python.exe scripts/inpaint_segment.py --src clip.MP4 --start 14 --dur 3 --speed 1 --fps 30 \
        --crop 608 1080 664 0 --size 1080 1920 --points '[[0.64,0.17],[0.72,0.22]]' --out part.mp4

What it does (called by cut_rough.py for segments that have "inpaint" in video.json, never by hand in a pipeline run):
 1. reads the moment at the output frame rate and keeps only the part of the picture the short will show (the crop box, native
    pixels), so nothing is processed that will not be seen;
 2. SAM2 (video predictor) turns one click per object, given in source-frame coordinates (0..1) at the first frame, into a mask that
    follows the object while the camera moves; clicks outside the crop are ignored;
 3. ProPainter (flow-guided video inpainting) fills only a small window around the masks, never the whole picture;
 4. the filled pixels are pasted back through a feathered mask, so everything outside the mask stays the original sharp footage;
 5. the result is scaled to the output size and written as a video-only mp4.
Environment: <tools> = plate-and-price/_tools (outside git) with `venv` (python 3.11, torch cu124, ultralytics, opencv, faster-whisper)
and `ProPainter` (git clone of github.com/sczhou/ProPainter with weights in ProPainter/weights). Override with the env variables
INPAINT_PYTHON and PROPAINTER_DIR. About 3-6 s per frame at 960x540; the window keeps it far smaller here.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()
PROPAINTER = Path(os.environ.get("PROPAINTER_DIR", Path(__file__).resolve().parents[3] / "_tools" / "ProPainter"))


def read_slice(a, frames_dir):
    n_blend = max(int(a.shutter), 1)
    blend = f"tmix=frames={n_blend}:weights='{' '.join(['1'] * n_blend)}'," if n_blend > 1 else ""
    fast = f"setpts=PTS/{a.speed}," if a.speed != 1 else ""
    cw, ch, x, y = a.crop
    n = int(round(a.dur * a.fps))
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(a.start), "-t", f"{a.dur * a.speed:.3f}", "-i", a.src, "-vf",
                    f"{blend}{fast}fps={a.fps},crop={cw}:{ch}:{x}:{y}", "-frames:v", str(n), str(frames_dir / "%05d.png")],
                   check=True)
    return sorted(frames_dir.glob("*.png"))


def object_masks(frames, a, tmp):
    """Union of the SAM2 masks of every clicked object, one boolean mask per frame, at the native slice size."""
    from ultralytics.models.sam import SAM2VideoPredictor
    cw, ch, x, y = a.crop
    sw, sh = a.src_size
    scale = min(1.0, 960.0 / ch)  # SAM2 works on a proxy video; 960 px tall is plenty for a mask
    pw, ph = int(round(cw * scale / 2)) * 2, int(round(ch * scale / 2)) * 2
    proxy = tmp / "proxy.mp4"
    w = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{pw}x{ph}", "-r", str(a.fps), "-i",
                          "pipe:0", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(proxy)], stdin=subprocess.PIPE)
    for f in frames:
        w.stdin.write(cv2.resize(cv2.imread(str(f)), (pw, ph), interpolation=cv2.INTER_AREA).tobytes())
    w.stdin.close()
    w.wait()
    union = np.zeros((len(frames), ch, cw), bool)
    for (nx, ny) in a.points:
        px, py = (nx * sw - x) * scale, (ny * sh - y) * scale  # source-frame fraction -> proxy pixels
        if not (0 <= px < pw and 0 <= py < ph):
            print(f"  click ({nx:.2f},{ny:.2f}) is outside the crop: skipped", flush=True)
            continue
        pred = SAM2VideoPredictor(overrides=dict(conf=0.25, task="segment", mode="predict", imgsz=1024, model="sam2.1_t.pt",
                                                 save=False, verbose=False))
        for i, r in enumerate(pred(source=str(proxy), points=[px, py], labels=[1], stream=True)):
            if i < len(frames) and r.masks is not None:
                m = r.masks.data.cpu().numpy().any(0).astype(np.uint8)
                union[i] |= cv2.resize(m, (cw, ch), interpolation=cv2.INTER_NEAREST) > 0
        print(f"  object ({nx:.2f},{ny:.2f}): masked in {int(union.any((1, 2)).sum())} of {len(frames)} frames", flush=True)
    return union


def inpaint_window(frames, union, a, tmp):
    """ProPainter on the window that holds every mask; returns {frame_index: filled window (native size)} and the window box."""
    cw, ch, _, _ = a.crop
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * a.dilate + 1, 2 * a.dilate + 1))
    masks = [cv2.dilate(m.astype(np.uint8) * 255, k) for m in union]
    ys, xs = np.nonzero(np.any(np.stack(masks) > 0, axis=0))
    if len(xs) == 0:
        return None, None, masks
    m_ = a.margin
    x0, x1 = max(int(xs.min()) - m_, 0), min(int(xs.max()) + m_, cw)
    y0, y1 = max(int(ys.min()) - m_, 0), min(int(ys.max()) + m_, ch)
    x0, y0 = x0 // 8 * 8, y0 // 8 * 8
    x1, y1 = min(-(-x1 // 8) * 8, cw // 8 * 8), min(-(-y1 // 8) * 8, ch // 8 * 8)
    ww, wh = x1 - x0, y1 - y0
    s = min(1.0, a.window_max / max(ww, wh))  # ProPainter works at most at window_max px on the long side
    tw, th = max(int(round(ww * s / 8)) * 8, 64), max(int(round(wh * s / 8)) * 8, 64)
    fdir, mdir, odir = tmp / "win", tmp / "winmask", tmp / "winout"
    fdir.mkdir(), mdir.mkdir()
    for i, f in enumerate(frames):
        im = cv2.imread(str(f))[y0:y1, x0:x1]
        cv2.imwrite(str(fdir / f"{i:05d}.png"), cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA))
        cv2.imwrite(str(mdir / f"{i:05d}.png"), cv2.resize(masks[i][y0:y1, x0:x1], (tw, th), interpolation=cv2.INTER_NEAREST))
    subprocess.run([sys.executable, "inference_propainter.py", "--video", str(fdir), "--mask", str(mdir), "--output", str(odir),
                    "--fp16", "--subvideo_length", "40", "--neighbor_length", "8", "--ref_stride", "12", "--raft_iter", "12",
                    "--mask_dilation", "2", "--save_frames"], cwd=str(PROPAINTER), check=True)
    out = sorted((odir / "win" / "frames").glob("*.png"))
    filled = [cv2.resize(cv2.imread(str(p)), (ww, wh), interpolation=cv2.INTER_CUBIC) for p in out]
    return filled, (x0, y0, x1, y1), masks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--shutter", type=int, default=1)
    ap.add_argument("--crop", type=int, nargs=4, required=True, metavar=("CW", "CH", "X", "Y"))
    ap.add_argument("--src-size", type=int, nargs=2, required=True, metavar=("W", "H"))
    ap.add_argument("--size", type=int, nargs=2, required=True, metavar=("W", "H"))
    ap.add_argument("--points", required=True, help="JSON [[x,y],...] in source-frame fractions at the first frame")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dilate", type=int, default=12, help="mask growth in native pixels, to cover shadows and edges")
    ap.add_argument("--margin", type=int, default=48)
    ap.add_argument("--window-max", type=int, default=512)
    a = ap.parse_args()
    a.points = json.loads(a.points)
    a.src_size = tuple(a.src_size)
    W, H = a.size
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fdir = tmp / "frames"
        fdir.mkdir()
        frames = read_slice(a, fdir)
        if not frames:
            raise SystemExit(f"no frames read from {a.src} at {a.start} s")
        union = object_masks(frames, a, tmp)
        filled, box, masks = inpaint_window(frames, union, a, tmp)
        writer = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(a.fps),
                                   "-i", "pipe:0", "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
                                   str(a.out)], stdin=subprocess.PIPE)
        for i, f in enumerate(frames):
            im = cv2.imread(str(f))
            if filled is not None and i < len(filled):
                x0, y0, x1, y1 = box
                soft = cv2.GaussianBlur(masks[i][y0:y1, x0:x1].astype(np.float32) / 255.0, (0, 0), 4)[..., None]
                im[y0:y1, x0:x1] = (im[y0:y1, x0:x1] * (1 - soft) + filled[i] * soft).astype(np.uint8)
            writer.stdin.write(cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4).tobytes())
        writer.stdin.close()
        writer.wait()
    print(f"inpainted {len(frames)} frames -> {a.out}", flush=True)


if __name__ == "__main__":
    main()
