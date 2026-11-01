"""Stage 1-2: pick the moments and join them in order into a rough cut (no cover, captions, music or cleaning yet).

usage: python cut_rough.py <video-id> --format short|short_ia|video [--force]
Reads input/<id>/video.json formats.<format>.segments: each is {src, src_start, dur[, cx]} where src is a recording in
input/<id>/ (default: meta["raw"]), layout ("fill" or "blurpad" for this clip only: blurpad keeps the whole width of a
wide clip over a blurred copy, for example a final wide shot in a vertical short), cx (0..1, default 0.5) says where to crop sideways when a wide clip goes into a
vertical short. Segments are joined in the order listed, which is the order they were filmed (file name = recording
order). The clip's own sound is kept, with a very short fade at each join so nothing clicks.
"crop" (default 1), "cx" and "cy" (0..1, default 0.5): crop is a zoom factor, 1.25 keeps the central 80 % of the picture, and cx/cy
choose which part of it is kept (0 = left/top edge, 1 = right/bottom edge). The output size never changes (1080x1920 short, 1920x1080 video) and the picture always fills the whole frame, with nothing empty at the edges:
crop below 1 is refused and cx/cy are kept inside 0..1. Use it in the short and in the horizontal video to leave
out something that should not be seen (a name, clutter, a person, the edge of the counter) or to tighten a shot. The whole
camera frame does not have to appear.
"speed" (default 1; 2 plays the moment twice as fast, 0.5 is slow motion: the 120 fps recordings allow smooth slow motion down to
0.25, use "shutter": 1 for it): a slow moment such as chopping an onion or garlic can be sped up so it takes
fewer seconds on screen. "dur" is always the length on screen; the clip is read for dur * speed source seconds. Decide it at the
selection stage, and the critics may ask for it ([shots] lever).
"shutter" (default 1; a segment may set its own, for a fast move that must stay sharp) blends that many source frames into each output frame, like a slower shutter: the sparkle of
small bright reflections that appears when a 120 fps recording is simply thinned to 30 fps goes away.
"inpaint" ({"points": [[x, y], ...]}, optional "dilate"): remove objects that should not be seen and fill the background in. Each point is one
click on an unwanted object in source-frame fractions (0..1) at the first frame of the moment; SAM2 follows it while the camera moves
and ProPainter fills a small window around it (scripts/inpaint_segment.py, local GPU, needs the _tools environment). Prefer a
different cx or crop first (directives 27 and 29): inpainting is for what is still inside the visible slice. The sound of the clip is not
used for such a format, like the AI-upscaled one.
Output layer: <OUTPUT_DIR>/<id>/layers/rough_<format>.mp4 (also copied to <OUTPUT_DIR>/<id>/rough_<format>.mp4).
It is cached: only a change to the segments, the layout or the recordings rebuilds it.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from common import OUTPUT_DIR, find_ffmpeg, fmt, load_json, probe_size, run, video_dir
from layers import build_cached, code, digest, picture_segments, quick, sig

CUT = ["-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"]


def clip_seconds(ffmpeg, path):
    err = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, sec = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(sec)


def build_rough(tmp, ffmpeg, vdir, raw, f_):
    W, H, fps = f_["w"], f_["h"], f_["fps"]
    cmd, chains = [ffmpeg, "-hide_banner", "-y"], []
    for i, s in enumerate(f_["segments"]):
        n_blend = s.get("shutter", f_.get("shutter", 1))  # source frames (120 fps) blended into each output frame; 1 = sharp
        blend = f"tmix=frames={n_blend}:weights='{' '.join(['1'] * n_blend)}'," if n_blend > 1 else ""
        speed = float(s.get("speed", 1))
        fast = f"setpts=PTS/{speed}," if speed != 1 else ""  # after the blend, before the frame-rate conversion
        cmd += ["-ss", str(s["src_start"]), "-t", f"{s['dur'] * speed:.3f}", "-i", str(vdir / s.get("src", raw))]
        if s.get("layout", f_["layout"]) == "blurpad":  # same recipe as the final footage: sharp clip over a blurred copy
            vf = (f"[{i}:v]{blend}{fast}fps={fps},split[b{i}][f{i}];[b{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"boxblur=30:5[bb{i}];[f{i}]scale={W}:{H}:force_original_aspect_ratio=decrease[ff{i}];"
                  f"[bb{i}][ff{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]")
        else:  # fill: scale up to cover the frame, crop sideways around cx
            cx, cy = min(max(float(s.get("cx", 0.5)), 0.0), 1.0), min(max(float(s.get("cy", 0.5)), 0.0), 1.0)  # inside the picture
            zoom = float(s.get("crop", 1))
            if zoom < 1:  # zooming out would leave empty edges: the frame must always be completely filled
                raise SystemExit(f"segment {i + 1}: crop {zoom} is below 1; use blurpad layout to show a wider picture instead")  # >1 keeps only the part of the picture at (cx, cy): 1.25 keeps 80 % of the frame
            vf = (f"[{i}:v]{blend}{fast}fps={fps},scale=ceil({W}*{zoom}/2)*2:ceil({H}*{zoom}/2)*2:force_original_aspect_ratio=increase:flags=lanczos,"
                  f"crop={W}:{H}:x='(iw-{W})*{cx}':y='(ih-{H})*{cy}',setsar=1,format=yuv420p[v{i}]")
        d = s["dur"]
        tempo = ""
        if speed != 1:  # atempo takes 0.5-2 per step: chain steps for bigger changes (slow motion below 0.5 keeps 0.5 for the sound)
            r, steps = max(speed, 0.5), []
            while r > 2.0:
                steps.append("atempo=2.0")
                r /= 2.0
            steps.append(f"atempo={r:.4f}")
            tempo = ",".join(steps) + ","
        af = (f"[{i}:a]{tempo}aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              f"afade=t=in:st=0:d=0.04,afade=t=out:st={d - 0.04:.2f}:d=0.04[a{i}]")
        chains += [vf, af]
    n = len(f_["segments"])
    chains.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vout][aout]")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "graph.txt").write_text(";\n".join(chains), encoding="utf-8")
        run(cmd + ["-/filter_complex", "graph.txt", "-map", "[vout]", "-map", "[aout]", *CUT, "-r", str(fps),
                   "-movflags", "+faststart", str(tmp)], cwd=d)


def crop_box(src_w, src_h, W, H, zoom, cx, cy):
    """The part of a source frame that fills a W x H output at this zoom, as even (w, h, x, y) in source pixels."""
    ch = int(round(src_h / zoom / 2)) * 2
    cw = int(round(ch * W / H / 2)) * 2
    cw, ch = min(cw, src_w), min(ch, src_h)
    return cw, ch, int(round((src_w - cw) * cx)), int(round((src_h - ch) * cy))


def build_segment_ai(out, ffmpeg, vdir, raw, f_, s, i, ai):
    """One segment, upscaled frame by frame with Real-ESRGAN (realesrgan-ncnn-py, local GPU, no cloud): ffmpeg reads the cropped
    native-resolution pixels, the network doubles them, they are resized to the output size and encoded. Video only."""
    from PIL import Image
    from realesrgan_ncnn_py import Realesrgan
    W, H, fps = f_["w"], f_["h"], f_["fps"]
    src = vdir / s.get("src", raw)
    sw, sh = probe_size(src)
    speed = float(s.get("speed", 1))
    n_blend = s.get("shutter", f_.get("shutter", 1))
    blend = f"tmix=frames={n_blend}:weights='{' '.join(['1'] * n_blend)}'," if n_blend > 1 else ""
    fast = f"setpts=PTS/{speed}," if speed != 1 else ""
    cx, cy = min(max(float(s.get("cx", 0.5)), 0.0), 1.0), min(max(float(s.get("cy", 0.5)), 0.0), 1.0)
    zoom = float(s.get("crop", 1))
    if zoom < 1:
        raise SystemExit(f"segment {i + 1}: crop {zoom} is below 1; use blurpad layout to show a wider picture instead")
    cw, ch, x, y = crop_box(sw, sh, W, H, zoom, cx, cy)
    n_frames = int(round(s["dur"] * fps))
    reader = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", str(s["src_start"]), "-t", f"{s['dur'] * speed:.3f}",
                               "-i", str(src), "-vf", f"{blend}{fast}fps={fps},crop={cw}:{ch}:{x}:{y}", "-frames:v", str(n_frames),
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], stdout=subprocess.PIPE)
    writer = subprocess.Popen([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(fps), "-i", "pipe:0", "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p",
                               "-r", str(fps), str(out)], stdin=subprocess.PIPE)
    net = Realesrgan(gpuid=0, model=ai.get("model", 0))
    size, done = cw * ch * 3, 0
    while True:
        buf = reader.stdout.read(size)
        if len(buf) < size:
            break
        up = net.process_pil(Image.frombytes("RGB", (cw, ch), buf)).resize((W, H), Image.LANCZOS)
        writer.stdin.write(up.tobytes())
        done += 1
    writer.stdin.close()
    reader.stdout.close()
    reader.wait()
    writer.wait()
    if done == 0:
        raise SystemExit(f"segment {i + 1}: no frames were read from {src.name} at {s['src_start']} s")
    print(f"  upscaled segment {i + 1}: {done} frames ({cw}x{ch} -> {W}x{H})", flush=True)


def inpaint_python():
    """Python of the inpainting environment (PyTorch + SAM2 + ProPainter), outside git: plate-and-price/_tools/venv."""
    default = Path(__file__).resolve().parents[3] / "_tools" / "venv" / "Scripts" / "python.exe"
    return os.environ.get("INPAINT_PYTHON", str(default))


def build_segment_inpaint(out, vdir, raw, f_, s, i):
    """One segment with unwanted objects removed: only the part of the picture that the format shows is processed."""
    W, H, fps = f_["w"], f_["h"], f_["fps"]
    src = vdir / s.get("src", raw)
    sw, sh = probe_size(src)
    cx, cy = min(max(float(s.get("cx", 0.5)), 0.0), 1.0), min(max(float(s.get("cy", 0.5)), 0.0), 1.0)
    zoom = float(s.get("crop", 1))
    if zoom < 1:
        raise SystemExit(f"segment {i + 1}: crop {zoom} is below 1; use blurpad layout to show a wider picture instead")
    cw, ch, x, y = crop_box(sw, sh, W, H, zoom, cx, cy)
    spec = s["inpaint"]
    cmd = [inpaint_python(), str(Path(__file__).with_name("inpaint_segment.py")), "--src", str(src), "--start", str(s["src_start"]),
           "--dur", str(s["dur"]), "--speed", str(s.get("speed", 1)), "--fps", str(fps), "--shutter", str(s.get("shutter", f_.get("shutter", 1))),
           "--crop", str(cw), str(ch), str(x), str(y), "--src-size", str(sw), str(sh), "--size", str(W), str(H),
           "--points", json.dumps(spec["points"]), "--out", str(out)]
    if "dilate" in spec:
        cmd += ["--dilate", str(spec["dilate"])]
    subprocess.run(cmd, check=True)
    print(f"  inpainted segment {i + 1}: {len(spec['points'])} object(s)", flush=True)


def build_rough_ai(tmp, ffmpeg, vdir, raw, f_):
    """Rough cut built segment by segment (AI-upscaled and/or inpainted footage): segments are made one by one (blurpad ones with the normal filter graph), joined with
    the concat demuxer, and a silent audio track is added (the sound of the clips is not used in the final)."""
    ai = f_.get("ai_upscale")
    with tempfile.TemporaryDirectory() as d:
        parts = []
        for i, s in enumerate(f_["segments"]):
            part = Path(d) / f"seg{i:03d}.mp4"
            if s.get("layout", f_["layout"]) == "blurpad":
                build_rough(part, ffmpeg, vdir, raw, {**f_, "segments": [s]})
            elif "inpaint" in s:
                build_segment_inpaint(part, vdir, raw, f_, s, i)
            elif ai:
                build_segment_ai(part, ffmpeg, vdir, raw, f_, s, i, ai)
            else:
                build_rough(part, ffmpeg, vdir, raw, {**f_, "segments": [s]})
            parts.append(part)
        (Path(d) / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
        total = sum(s["dur"] for s in f_["segments"])
        run([ffmpeg, "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-f", "lavfi", "-t", f"{total:.3f}",
             "-i", "anullsrc=r=48000:cl=stereo", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
             "-shortest", "-movflags", "+faststart", str(tmp)], cwd=d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "short_ia", "video"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, a.format)
    raw = meta.get("raw")
    srcs = sorted({s.get("src", raw) for s in f_["segments"]})
    ffmpeg = find_ffmpeg()
    length = {n: clip_seconds(ffmpeg, vdir / n) for n in srcs}
    for s in f_["segments"]:  # a cut that runs past the end of a clip would silently come out short
        n = s.get("src", raw)
        used = s["dur"] * float(s.get("speed", 1))
        if s["src_start"] + used > length[n] + 0.05:
            raise SystemExit(f"{n}: {s['src_start']} + {used:g} s runs past the end of the clip ({length[n]:.1f} s)")
    out_dir = OUTPUT_DIR / a.video_id
    layer = out_dir / "layers" / f"rough_{a.format}.mp4"
    ai = f_.get("ai_upscale")
    inpaint = any("inpaint" in s for s in f_["segments"])
    mixed = bool(ai) or inpaint  # built segment by segment, the clips' own sound is not used
    ipk = (code(build_segment_inpaint), sig(Path(__file__).with_name("inpaint_segment.py"))) if inpaint else ""
    key = digest("rough", code(build_rough), code(build_rough_ai) + code(build_segment_ai) if mixed else "", ai or "", ipk, [quick(vdir / s) for s in srcs], picture_segments(f_["segments"]), f_.get("shutter", 1), f_["layout"], f_["w"], f_["h"], f_["fps"], raw)
    build = build_rough_ai if mixed else build_rough
    build_cached(layer, key, lambda t: build(t, ffmpeg, vdir, raw, f_), f"rough cut {a.format}" + (" (AI upscaled)" if ai else "") + (" (objects removed)" if inpaint else ""), a.force)
    final = out_dir / f"rough_{a.format}.mp4"
    shutil.copyfile(layer, final)
    footage = sum(s["dur"] for s in f_["segments"])
    print(f"rough={final} ({len(f_['segments'])} clips, {footage:.1f} s of footage; cover and end card add {f_['cover_dur'] + f_['endcard_dur']} s)")
    if ai:  # the ncnn/Vulkan library can crash while it is torn down at exit, after the layer is finished: leave without that
        sys.stdout.flush()
        os._exit(0)


if __name__ == "__main__":
    main()
