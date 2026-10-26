"""Build the evidence a reviewer needs to judge a finished short or video, without watching it: a numbered contact sheet,
the caption timeline and measured pacing numbers.

usage: python review_pack.py <video-id> --format short|video --lang en
Output (in <OUTPUT_DIR>/<id>/review/): <format>_<lang>_sheet_N.jpg (one frame per second, time-stamped), and
<format>_<lang>_facts.md (length, number of cuts and average shot length, caption reading speed, loudness, which clips
come from which recording, the hook window). The reviewer roles in review/roles/*.md read these files.
"""
import argparse
import re
import subprocess

from PIL import Image, ImageDraw

from common import OUTPUT_DIR, find_ffmpeg, fmt, load_json, parse_srt, video_dir


def run_text(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, a.format)
    ff = find_ffmpeg()
    src = OUTPUT_DIR / a.video_id / f"{a.format}_{a.lang}.mp4"
    out = OUTPUT_DIR / a.video_id / "review"
    out.mkdir(exist_ok=True)
    frames = out / f"frames_{a.format}_{a.lang}"
    frames.mkdir(exist_ok=True)
    for p in frames.glob("*.jpg"):
        p.unlink()
    w = 216 if f_["h"] > f_["w"] else 384
    h = 384 if f_["h"] > f_["w"] else 216
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-vf", f"fps=1,scale={w}:{h}",
                    str(frames / "f%03d.jpg")], check=True)
    files = sorted(frames.glob("f*.jpg"))
    per_row, rows = (8, 3) if h > w else (5, 4)
    per_sheet = per_row * rows
    for n in range(0, len(files), per_sheet):
        chunk = files[n:n + per_sheet]
        sheet = Image.new("RGB", (per_row * w, ((len(chunk) - 1) // per_row + 1) * h), "black")
        d = ImageDraw.Draw(sheet)
        for i, fp in enumerate(chunk):
            x, y = (i % per_row) * w, (i // per_row) * h
            sheet.paste(Image.open(fp), (x, y))
            d.rectangle((x, y, x + 46, y + 14), fill="black")
            d.text((x + 3, y + 2), f"{n + i}s", fill="yellow")
        sheet.save(out / f"{a.format}_{a.lang}_sheet_{n // per_sheet + 1}.jpg", quality=82)
    cues = parse_srt(vdir / f_["captions"][a.lang])
    total = f_["total"]
    segs = f_["segments"]
    cuts = len(segs) + 1  # cover, clips, end card
    avg_shot = sum(s["dur"] for s in segs) / len(segs)
    speeds = [len(re.sub(r"\s+", "", t)) / max(b - a_, 0.1) for a_, b, t in cues]
    vol = run_text([ff, "-hide_banner", "-i", str(src), "-af", "volumedetect", "-vn", "-f", "null", "-"])
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
    lines = [f"# Facts for {a.video_id} {a.format} {a.lang}", "",
             f"- Length {total:.0f} s; cover {f_['cover_dur']} s, {len(segs)} clips of {avg_shot:.1f} s on average, end card {f_['endcard_dur']} s.",
             f"- Cuts per minute: {cuts / total * 60:.0f}.",
             f"- First caption appears at {cues[0][0]:.1f} s; the hook window (first 3 s) is the cover only." if cues and cues[0][0] >= f_["cover_dur"]
             else "- A caption is on screen in the first seconds.",
             f"- Captions: {len(cues)}, reading speed {sum(speeds) / len(speeds):.0f} characters/s on average (comfortable is under about 17).",
             f"- Mean loudness {mean.group(1) if mean else '?'} dB (music and voice).",
             f"- Audio: {meta['audio'].get('song', {}).get('title', 'none')} (licensed: {meta['audio'].get('song', {}).get('licensed')}).", "",
             "## Timeline (clip, source file, what it shows)"]
    t = f_["cover_dur"]
    lines.append("- 0.0 s cover card (AI image, title, price per serving)")
    for s in segs:
        lines.append(f"- {t:.1f} s {s.get('src', '')} from {s['src_start']} s for {s['dur']} s: {s.get('note', '')}")
        t += s["dur"]
    lines.append(f"- {t:.1f} s end card (ingredient prices and total)")
    lines += ["", "## Captions"] + [f"- {a_:.1f}-{b:.1f} s: {tx.replace(chr(10), ' ')}" for a_, b, tx in cues]
    (out / f"{a.format}_{a.lang}_facts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"review pack in {out}")


if __name__ == "__main__":
    main()
