"""Stage 1-2: pick the moments and join them in order into a rough cut (no cover, captions, music or cleaning yet).

usage: python cut_rough.py <video-id> --format short|video [--force]
Reads input/<id>/video.json formats.<format>.segments: each is {src, src_start, dur[, cx]} where src is a recording in
input/<id>/ (default: meta["raw"]), cx (0..1, default 0.5) says where to crop sideways when a wide clip goes into a
vertical short. Segments are joined in the order listed, which is the order they were filmed (file name = recording
order). The clip's own sound is kept, with a very short fade at each join so nothing clicks.
Output layer: <OUTPUT_DIR>/<id>/layers/rough_<format>.mp4 (also copied to <OUTPUT_DIR>/<id>/rough_<format>.mp4).
It is cached: only a change to the segments, the layout or the recordings rebuilds it.
"""
import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import OUTPUT_DIR, find_ffmpeg, fmt, load_json, run, video_dir
from layers import build_cached, code, digest, quick

CUT = ["-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"]


def clip_seconds(ffmpeg, path):
    err = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, sec = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(sec)


def build_rough(tmp, ffmpeg, vdir, raw, f_):
    W, H, fps = f_["w"], f_["h"], f_["fps"]
    cmd, chains = [ffmpeg, "-hide_banner", "-y"], []
    for i, s in enumerate(f_["segments"]):
        cmd += ["-ss", str(s["src_start"]), "-t", str(s["dur"]), "-i", str(vdir / s.get("src", raw))]
        if f_["layout"] == "blurpad":  # same recipe as the final footage: sharp clip over a blurred copy
            vf = (f"[{i}:v]fps={fps},split[b{i}][f{i}];[b{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"boxblur=30:5[bb{i}];[f{i}]scale={W}:{H}:force_original_aspect_ratio=decrease[ff{i}];"
                  f"[bb{i}][ff{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]")
        else:  # fill: scale up to cover the frame, crop sideways around cx
            cx = s.get("cx", 0.5)
            vf = (f"[{i}:v]fps={fps},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                  f"crop={W}:{H}:x='(iw-{W})*{cx}':y='(ih-{H})/2',setsar=1,format=yuv420p[v{i}]")
        d = s["dur"]
        af = (f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
              f"afade=t=in:st=0:d=0.04,afade=t=out:st={d - 0.04:.2f}:d=0.04[a{i}]")
        chains += [vf, af]
    n = len(f_["segments"])
    chains.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vout][aout]")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "graph.txt").write_text(";\n".join(chains), encoding="utf-8")
        run(cmd + ["-filter_complex_script", "graph.txt", "-map", "[vout]", "-map", "[aout]", *CUT, "-r", str(fps),
                   "-movflags", "+faststart", str(tmp)], cwd=d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
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
        if s["src_start"] + s["dur"] > length[n] + 0.05:
            raise SystemExit(f"{n}: {s['src_start']} + {s['dur']} s runs past the end of the clip ({length[n]:.1f} s)")
    out_dir = OUTPUT_DIR / a.video_id
    layer = out_dir / "layers" / f"rough_{a.format}.mp4"
    key = digest("rough", code(build_rough), [quick(vdir / s) for s in srcs], f_["segments"], f_["layout"], f_["w"], f_["h"], f_["fps"], raw)
    build_cached(layer, key, lambda t: build_rough(t, ffmpeg, vdir, raw, f_), f"rough cut {a.format}", a.force)
    final = out_dir / f"rough_{a.format}.mp4"
    shutil.copyfile(layer, final)
    footage = sum(s["dur"] for s in f_["segments"])
    print(f"rough={final} ({len(f_['segments'])} clips, {footage:.1f} s of footage; cover and end card add {f_['cover_dur'] + f_['endcard_dur']} s)")


if __name__ == "__main__":
    main()
