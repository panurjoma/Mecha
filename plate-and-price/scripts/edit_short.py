"""Edit one product from the raw footage: cover, zoom clips, burned-in captions, price end card, music (and voice-over).

usage: python edit_short.py <video-id> --format short|video --lang en
Settings come from input/<id>/video.json formats.<format>:
  short = 1080x1920 for YouTube Shorts: cover 2 s, 3 s clips with zoom, captions + music.
  video = 1920x1080 for the YouTube channel: footage in the middle over a blurred copy of itself, longer calmer clips,
          captions + voice-over (music lowered underneath). The voice is voice_<format>_<lang>.wav (your own recording)
          if present, else voice_<format>_tts_<lang>.wav from make_voice.py.
Writes <OUTPUT_DIR>/<id>/<format>_<lang>.mp4 (master) and <format>_<lang>_review.mp4 (small, for email).
"""
import argparse
import tempfile
from pathlib import Path

from common import OUTPUT_DIR, find_ffmpeg, fmt, load_json, parse_srt, probe_size, run, video_dir


def ass_time(t):
    cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def write_ass(path, cues, w, h, st):
    head = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
        "MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Cap,{st['font']},{st['size']},&H00FFFFFF,&H00FFFFFF,&H00202020,&H80000000,"
        f"{-1 if st.get('bold', True) else 0},0,0,0,100,100,0,0,1,{st['outline']},2,{st['align']},60,60,{st['margin_v']},1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    lines = [f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{{\\fad(120,120)}}{t.replace(chr(10), chr(92) + 'N')}"
             for a, b, t in cues]
    Path(path).write_text(head + "\n".join(lines) + "\n", encoding="utf-8")


def zoom_expr(kind, frames, amount):
    return f"1+{amount}*on/{frames}" if kind == "in" else f"1+{amount}-{amount}*on/{frames}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    kind = a.format

    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, kind)
    o = f_["output"]
    W, H, fps = f_["w"], f_["h"], f_["fps"]
    raw = vdir / meta["raw"]
    rw, rh = probe_size(raw)
    cues = parse_srt(vdir / f_["captions"][a.lang])
    pick = lambda stem: next((p for p in (vdir / f"{stem}_{kind}.png", vdir / f"{stem}_{kind}_{a.lang}.png") if p.exists()), None)
    cover, endcard = pick("cover"), pick("endcard")
    if cover is None or endcard is None:
        raise SystemExit("missing cover or end card: run make_cover.py and make_endcard.py first (run_pipeline.py does it)")
    ffmpeg = find_ffmpeg()
    out_dir = OUTPUT_DIR / a.video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    enh = meta.get("enhance", {})
    enhance = []
    if enh.get("denoise"):
        enhance.append("hqdn3d=1.5:1.5:6:6")
    if enh.get("sharpen"):
        enhance.append(f"unsharp=5:5:{enh['sharpen']}:5:5:0")
    enhance.append(f"eq=saturation={enh.get('saturation', 1.0)}:contrast={enh.get('contrast', 1.0)}")
    amount = f_["zoom_amount"]
    total = f_["total"]

    cmd = [ffmpeg, "-hide_banner", "-y"]
    chains, labels = [], []

    def still(img, dur, label, zoom_to):
        cmd.extend(["-loop", "1", "-framerate", str(fps), "-t", str(dur), "-i", str(img)])
        i, n = len(labels), round(dur * fps)
        chains.append(f"[{i}:v]scale={W * 2}:{H * 2}:flags=lanczos,zoompan=z='1+{zoom_to}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                      f":d=1:s={W}x{H}:fps={fps},fade=t=in:st=0:d=0.3,setsar=1,format=yuv420p[{label}]")
        labels.append(label)

    def clip(s):
        cmd.extend(["-ss", str(s["src_start"]), "-t", str(s["dur"]), "-i", str(raw)])
        i, n = len(labels), round(s["dur"] * fps)
        z = f"zoompan=z='{zoom_expr(s['zoom'], n, amount)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1"
        if f_["layout"] == "blurpad":  # sharp footage centred over a blurred, darkened copy that fills the frame
            fw = round(H * rw / rh / 2) * 2
            chains.append(
                f"[{i}:v]fps={fps},split[bs{i}][fs{i}];"
                f"[bs{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,eq=brightness=-0.1[bb{i}];"
                f"[fs{i}]scale={fw * 2}:{H * 2}:flags=lanczos,{z}:s={fw}x{H}:fps={fps},{','.join(enhance)},setsar=1[fz{i}];"
                f"[bb{i}][fz{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]")
        else:
            chains.append(
                f"[{i}:v]fps={fps},scale={W * 2}:{H * 2}:flags=lanczos,{z}:s={W}x{H}:fps={fps},"
                f"{','.join(enhance)},setsar=1,format=yuv420p[v{i}]")
        labels.append(f"v{i}")

    still(cover, f_["cover_dur"], "vcover", 0.05)
    for s in f_["segments"]:
        clip(s)
    still(endcard, f_["endcard_dur"], "vend", 0.04)

    au = meta["audio"]
    cmd.extend(["-ss", str(au["start"]), "-t", str(total), "-i", str(raw if au["source"] == "raw" else vdir / au["source"])])
    music = len(labels)
    chains.append("".join(f"[{l}]" for l in labels) + f"concat=n={len(labels)}:v=1:a=0[vc]")
    chains.append("[vc]subtitles=captions.ass[vout]")
    fade = f"afade=t=out:st={total - au['fade_out']}:d={au['fade_out']}"
    if f_["voice"]:
        vfile = next((p for p in (vdir / f"voice_{kind}_{a.lang}.wav", vdir / f"voice_{kind}_tts_{a.lang}.wav") if p.exists()), None)
        if vfile is None:
            raise SystemExit("no voice: run make_voice.py or put voice_<format>_<lang>.wav in the input folder")
        cmd.extend(["-i", str(vfile)])
        chains.append(f"[{music}:a]volume={au['volume_with_voice']}[m];[{music + 1}:a]volume=1.4[vo];"
                      f"[m][vo]amix=inputs=2:duration=first:normalize=0,{fade}[aout]")
    else:
        chains.append(f"[{music}:a]volume={au['volume']},{fade}[aout]")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        write_ass(tmp / "captions.ass", cues, W, H, f_["caption_style"])
        (tmp / "graph.txt").write_text(";\n".join(chains), encoding="utf-8")
        master = out_dir / f"{kind}_{a.lang}.mp4"
        run(cmd + ["-filter_complex_script", "graph.txt", "-map", "[vout]", "-map", "[aout]",
                   "-c:v", "libx264", "-preset", "slow", "-crf", o["crf"], "-pix_fmt", "yuv420p",
                   "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-r", fps, str(master)], cwd=tmp)
    review = out_dir / f"{kind}_{a.lang}_review.mp4"
    run([ffmpeg, "-hide_banner", "-y", "-i", master, "-c:v", "libx264", "-b:v", o["review_bitrate"],
         "-maxrate", o["review_bitrate"], "-bufsize", "6000k", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", review])
    print(f"master={master}\nreview={review} ({review.stat().st_size / 1e6:.1f} MB, {total:.1f} s)")


if __name__ == "__main__":
    main()
