"""Build the evidence a reviewer needs to judge a finished short or video, without watching it: a numbered contact sheet,
the caption timeline and measured pacing numbers.

usage: python review_pack.py <video-id> --format short|short_ia|video --lang en
Output (in <OUTPUT_DIR>/<id>/review/): <format>_<lang>_sheet_N.jpg (one frame per second, time-stamped), and
<format>_<lang>_facts.md (length, number of cuts and average shot length, caption reading speed, loudness, which clips
come from which recording, the hook window). The four reviewer agents (.claude/agents/*.md) read these files.
It also writes sources_sheet_N.jpg (4 frames of every recording, numbered by file) the first time, so a reviewer can name a replacement shot.
"""
import argparse
import json
import re
import subprocess

from PIL import Image, ImageDraw

from common import OUTPUT_DIR, final_dir, find_ffmpeg, fmt, load_json, parse_srt, video_dir


def run_text(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stderr


def source_sheets(vdir, out, ff):
    """Contact sheets of all recordings in the input folder (4 frames each), built once."""
    if list(out.glob("sources_sheet_*.jpg")):
        return
    clips = sorted(p for p in vdir.iterdir() if p.suffix.lower() == ".mp4")
    rows = []
    for p in clips:
        err = run_text([ff, "-hide_banner", "-i", str(p)])
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
        dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        row = Image.new("RGB", (4 * 320, 180), "black")
        for i in range(4):
            tmp = out / "_f.jpg"
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{dur * (i + 0.5) / 4:.2f}", "-i", str(p),
                            "-frames:v", "1", "-vf", "scale=320:180", str(tmp)], check=True)
            row.paste(Image.open(tmp), (i * 320, 0))
        ImageDraw.Draw(row).text((4, 4), f"{p.stem} ({dur:.1f}s)", fill="yellow")
        rows.append(row)
    (out / "_f.jpg").unlink(missing_ok=True)
    for n in range(0, len(rows), 8):
        grp = rows[n:n + 8]
        sheet = Image.new("RGB", (4 * 320, len(grp) * 180))
        for i, row in enumerate(grp):
            sheet.paste(row, (0, i * 180))
        sheet.save(out / f"sources_sheet_{n // 8 + 1}.jpg", quality=80)


def loudness(ff, path):
    """Integrated loudness (LUFS), loudness range (LU) and true peak (dBTP) of a file, plus its mean volume."""
    err = run_text([ff, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"])
    tail = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    g = lambda pat: (re.search(pat, tail) or [None, "?"])[1]
    vol = run_text([ff, "-hide_banner", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-"])
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
    return {"lufs": g(r"I:\s+(-?[\d.]+) LUFS"), "lra": g(r"LRA:\s+([\d.]+) LU"), "tp": g(r"Peak:\s+(-?[\d.]+) dBFS"),
            "mean": mean.group(1) if mean else "?"}


def extra_facts(vdir, meta, f_, a, ff, src, out, cues):
    """Evidence for the audio, recipe-and-price and discoverability reviewers."""
    L = ["", "## Audio (measured; the reviewer cannot listen)"]
    m = loudness(ff, src)
    L.append(f"- Final mix: integrated {m['lufs']} LUFS, loudness range {m['lra']} LU, true peak {m['tp']} dBTP, mean volume {m['mean']} dB.")
    lay = OUTPUT_DIR / a.video_id / "layers"
    music = lay / f"music_{a.format}.wav"
    if music.exists():
        mm = loudness(ff, music)
        L.append(f"- Music layer alone (before volume and loudness steps): mean volume {mm['mean']} dB.")
    voice = next((p for p in (vdir / f"voice_{a.format}_{a.lang}.wav", vdir / f"voice_{a.format}_tts_{a.lang}.wav") if p.exists()), None)
    if f_["voice"] and voice:
        vm = loudness(ff, voice)
        L.append(f"- Voice-over alone: mean volume {vm['mean']} dB ({voice.name}); music is mixed at x{meta['audio']['volume_with_voice']} under it.")
        v = meta["voice"][a.lang]
        L.append(f"- Voice: {v['voice']} at rate {v['rate']} (male, calm); speech must fit each caption window.")
        L.append("- Voice lines (characters, window seconds, characters per second):")
        for s, e, t in cues:
            n = len(re.sub(r"\s+", " ", t.replace(chr(10), " ")))
            L.append(f"  - {n} chars in {e - s:.1f} s = {n / max(e - s, 0.1):.0f} chars/s: {t.replace(chr(10), ' ')}")
    else:
        L.append("- No voice-over in this format: the music carries the sound; the original kitchen sound is removed.")
    audio = {**meta["audio"], **f_.get("audio", {})}
    song = audio.get("song") or {}
    L.append(f"- Music: {song.get('title', 'none')} starts at {audio.get('start', 0)} s, fade-out {audio.get('fade_out')} s.")

    pj = vdir / "price.json"
    L += ["", "## Recipe and price (estimate, no receipts)"]
    if pj.exists():
        price = load_json(pj)
        total = round(sum(i["price"] for i in price["items"]), 2)
        L.append(f"- Servings: {price['servings']}. Total EUR {total:.2f}; per serving EUR {total / price['servings']:.2f}. Note: {price.get('_note', '')}")
        L += [f"  - {i['en']}: EUR {i['price']:.2f}" for i in price["items"]]
    rm = vdir / "recipe.md"
    if rm.exists():
        L += ["", "### recipe.md", rm.read_text(encoding="utf-8").strip()]

    L += ["", "## Discoverability (what YouTube will show)"]
    desc = final_dir(a.video_id) / f"description_{a.format}_{a.lang}.md"
    if desc.exists():
        L += ["```", desc.read_text(encoding="utf-8").strip(), "```"]
    else:
        L.append("- No description file yet: run make_description.py.")
    thumb = vdir / f"thumbnail_{a.lang}.png" if a.format == "video" else vdir / f"cover_{a.format}_{a.lang}.png"
    if thumb.exists():
        import shutil
        shutil.copyfile(thumb, out / f"{a.format}_{a.lang}_thumbnail.png")
        L.append(f"- Thumbnail/cover image to look at: {out / f'{a.format}_{a.lang}_thumbnail.png'}")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "short_ia", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, a.format)
    ff = find_ffmpeg()
    src = final_dir(a.video_id) / f"{a.format}_{a.lang}.mp4"
    out = OUTPUT_DIR / a.video_id / "review"
    out.mkdir(exist_ok=True)
    source_sheets(vdir, out, ff)
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
             (f"- A moving hook of {f_['hook_dur']} s opens the video, then the {f_['cover_dur']} s cover card." if f_["hook_dur"] else
              f"- The first {f_['cover_dur']} s are the still cover card (no hook shot)."),
             f"- First caption at {cues[0][0]:.1f} s." if cues else "- No captions.",
             f"- Captions: {len(cues)}, reading speed {sum(speeds) / len(speeds):.0f} characters/s on average (comfortable is under about 17).",
             f"- Mean loudness {mean.group(1) if mean else '?'} dB (music and voice).",
             f"- Audio: {meta['audio'].get('song', {}).get('title', 'none')} (licensed: {meta['audio'].get('song', {}).get('licensed')}).", "",
             f"- Caption style: {json.dumps(f_['caption_style'], ensure_ascii=False)}.",
             f"- Dedicated rough/clean path: {not meta.get('raw') or bool(f_.get('clean_first'))}; format clean settings: {json.dumps(f_.get('clean', {}))}.",
             "## Timeline (clip, source file, what it shows)"]
    t = 0.0
    if not f_["hook_dur"]:
        lines.append("- 0.0 s cover card (AI image, title, price per serving)")
        t = f_["cover_dur"]
    for i, s in enumerate(segs):
        tag = "HOOK (moving shot before the cover) " if i == 0 and f_["hook_dur"] else ""
        lines.append(f"- {t:.1f} s {tag}{s.get('src', meta.get('raw', ''))} from {s['src_start']} s for {s['dur']} s: {s.get('note', '')}")
        t += s["dur"]
        if i == 0 and f_["hook_dur"]:
            lines.append(f"- {t:.1f} s cover card (AI image, title, price per serving, {f_['cover_dur']} s)")
            t += f_["cover_dur"]
    lines.append(f"- {t:.1f} s end card (ingredient prices and total)")
    lines += ["", "## Captions"] + [f"- {a_:.1f}-{b:.1f} s: {tx.replace(chr(10), ' ')}" for a_, b, tx in cues]
    lines += extra_facts(vdir, meta, f_, a, ff, src, out, cues)
    (out / f"{a.format}_{a.lang}_facts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"review pack in {out}")


if __name__ == "__main__":
    main()
