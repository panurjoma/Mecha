"""Build one product (short or video) from separate layers, rebuilding only the layers whose inputs changed.

usage: python edit_short.py <video-id> --format short|video --lang en [--force captions,mix]

Layers (files in <OUTPUT_DIR>/<id>/layers/, each with a .key fingerprint; see layers.py):
  footage_<format>.mp4            the zoomed clips only (slow to build, language independent)
  still_<format>_<lang>_cover/endcard.mp4   the cover and price card as short clips
  captioned_<format>_<lang>.mp4   cover + footage + end card with the captions burned in (picture only, no sound)
  music_<format>.wav              the song, cut to length
  mix_<format>_<lang>.wav         music (+ voice-over for the video), faded out
Final files: <OUTPUT_DIR>/<id>/final/<format>_<lang>.mp4 (picture copied, audio encoded). When a rebuild replaces a file in
final/, the old one is first moved to <OUTPUT_DIR>/<id>/archive/ with a time stamp (directive 23). The small email copy
<format>_<lang>_review.mp4 goes to <OUTPUT_DIR>/<id>/email/.

What rebuilds when you change something:
  captions file or caption style -> captioned, final   (and the voice, because the voice reads the captions)
  voice (file or voice name)     -> mix, final          (seconds)
  song or music volume           -> music, mix, final
  cover or end card image        -> that still, captioned, final
  clips, zoom, layout, raw video -> footage, captioned, final
--force names layers to rebuild anyway: footage, stills, captions, music, mix, final, review, or all.
Settings come from input/<id>/video.json formats.<format>; see README for the layer table.
"""
import argparse
import tempfile
from pathlib import Path

from common import OUTPUT_DIR, archive_old, final_dir, find_ffmpeg, fmt, load_json, parse_srt, probe_size, run, video_dir
from layers import build_cached, code, digest, key_of, picture_segments, sig

LOUD = "loudnorm=I=-15:TP=-2.5:LRA=11"  # streaming-level loudness (the music alone was about -24 dB, too quiet for a phone)
CLIP = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-an"]  # near-lossless intermediates


def ass_time(t):
    cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def ass_color(hex_rgb, alpha="00"):
    """'FFE27A' (RGB) -> '&H00' + BGR as libass wants it."""
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"&H{alpha}{b}{g}{r}"


def write_ass(path, cues, w, h, st):
    # Brand colours improve phone readability; ASS stores colour in BGR order.
    colour = st.get("color", "#FFFFFF").lstrip("#")
    primary = f"&H00{colour[4:6]}{colour[2:4]}{colour[0:2]}"
    head = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
        "MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Cap,{st['font']},{st['size']},{primary},{primary},&H00202020,&H80000000,"
        f"{-1 if st.get('bold', True) else 0},0,0,0,100,100,0,0,1,{st['outline']},2,{st['align']},"
        f"{st.get('margin_l', 60)},{st.get('margin_r', 60)},{st['margin_v']},1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    lines = [f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{{\\fad(120,0)}}{t.replace(chr(10), chr(92) + 'N')}"
             for a, b, t in cues]
    Path(path).write_text(head + "\n".join(lines) + "\n", encoding="utf-8")


def zoom_expr(kind, frames, amount):
    return f"1+{amount}*on/{frames}" if kind == "in" else f"1+{amount}-{amount}*on/{frames}"


def enhance_filters(enh):
    out = []
    if enh.get("denoise"):
        out.append("hqdn3d=1.5:1.5:6:6")
    if enh.get("sharpen"):
        out.append(f"unsharp=5:5:{enh['sharpen']}:5:5:0")
    out.append(f"eq=saturation={enh.get('saturation', 1.0)}:contrast={enh.get('contrast', 1.0)}")
    return out


def build_footage(tmp, ffmpeg, raw, f_, enh, rw, rh):
    W, H, fps = f_["w"], f_["h"], f_["fps"]
    enhance = enhance_filters(enh)
    cmd, chains, labels = [ffmpeg, "-hide_banner", "-y"], [], []
    for i, s in enumerate(f_["segments"]):
        cmd += ["-ss", str(s["src_start"]), "-t", str(s["dur"]), "-i", str(raw)]
        n = round(s["dur"] * fps)
        z = f"zoompan=z='{zoom_expr(s['zoom'], n, f_['zoom_amount'])}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1"
        if f_["layout"] == "blurpad":  # sharp footage centred over a blurred, darkened copy that fills the frame
            fw = round(H * rw / rh / 2) * 2
            chains.append(
                f"[{i}:v]fps={fps},split[bs{i}][fs{i}];"
                f"[bs{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,eq=brightness=-0.1[bb{i}];"
                f"[fs{i}]scale={fw * 2}:{H * 2}:flags=lanczos,{z}:s={fw}x{H}:fps={fps},{','.join(enhance)},setsar=1[fz{i}];"
                f"[bb{i}][fz{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]")
        else:
            chains.append(f"[{i}:v]fps={fps},scale={W * 2}:{H * 2}:flags=lanczos,{z}:s={W}x{H}:fps={fps},"
                          f"{','.join(enhance)},setsar=1,format=yuv420p[v{i}]")
        labels.append(f"v{i}")
    chains.append("".join(f"[{l}]" for l in labels) + f"concat=n={len(labels)}:v=1:a=0[vout]")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "graph.txt").write_text(";\n".join(chains), encoding="utf-8")
        run(cmd + ["-filter_complex_script", "graph.txt", "-map", "[vout]", *CLIP, "-r", str(fps), str(tmp)], cwd=d)


def build_still(tmp, ffmpeg, img, dur, W, H, fps, zoom_to, fade_in=True):
    n = round(dur * fps)
    vf = (f"scale={W * 2}:{H * 2}:flags=lanczos,zoompan=z='1+{zoom_to}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d=1:s={W}x{H}:fps={fps}{',fade=t=in:st=0:d=0.3' if fade_in else ''},setsar=1,format=yuv420p")
    run([ffmpeg, "-hide_banner", "-y", "-loop", "1", "-framerate", str(fps), "-t", str(dur), "-i", str(img), "-vf", vf,
         *CLIP, "-r", str(fps), str(tmp)])


def build_captioned(tmp, ffmpeg, cover, footage, endcard, cues, f_):
    h = f_["hook_dur"]  # a moving hook plays first, then the cover card, then the rest of the footage
    with tempfile.TemporaryDirectory() as d:
        write_ass(Path(d) / "captions.ass", cues, f_["w"], f_["h"], f_["caption_style"])
        if h:
            graph = (f"[1:v]trim=0:{h},setpts=PTS-STARTPTS[hk];[1:v]trim=start={h},setpts=PTS-STARTPTS[rest];"
                     "[hk][0:v][rest][2:v]concat=n=4:v=1:a=0[vc];[vc]subtitles=captions.ass[vout]")
        else:
            graph = "[0:v][1:v][2:v]concat=n=3:v=1:a=0[vc];[vc]subtitles=captions.ass[vout]"
        (Path(d) / "graph.txt").write_text(graph, encoding="utf-8")
        run([ffmpeg, "-hide_banner", "-y", "-i", str(cover), "-i", str(footage), "-i", str(endcard),
             "-filter_complex_script", "graph.txt", "-map", "[vout]", "-c:v", "libx264", "-preset", "medium",
             "-crf", str(f_["output"]["crf"]), "-pix_fmt", "yuv420p", "-an", "-r", str(f_["fps"]), str(tmp)], cwd=d)


def build_music(tmp, ffmpeg, src, au, total):
    run([ffmpeg, "-hide_banner", "-y", "-ss", str(au["start"]), "-t", str(total), "-i", str(src), "-vn",
         "-af", "aformat=sample_rates=44100:channel_layouts=stereo", str(tmp)])


def build_mix(tmp, ffmpeg, music, voice, au, total):
    fade = f"afade=t=out:st={total - au['fade_out']}:d={au['fade_out']}"
    if voice:
        # ducking: the song plays about 2.5x louder in the gaps, the hook and the cover, and drops to volume_with_voice under speech
        graph = (f"[0:a]volume={au['volume_with_voice'] * 2.5:.3f}[m];[1:a]volume=1.4,asplit=2[vo][sc];"
                 f"[m][sc]sidechaincompress=threshold=0.05:ratio=2.5:attack=40:release=800[md];"
                 f"[md][vo]amix=inputs=2:duration=first:normalize=0,{LOUD},{fade}[a]")
        run([ffmpeg, "-hide_banner", "-y", "-i", str(music), "-i", str(voice), "-filter_complex", graph, "-map", "[a]", str(tmp)])
    else:
        run([ffmpeg, "-hide_banner", "-y", "-i", str(music), "-af", f"volume={au['volume']},{LOUD},{fade}", str(tmp)])


def build_final(tmp, ffmpeg, captioned, mix):
    run([ffmpeg, "-hide_banner", "-y", "-i", str(captioned), "-i", str(mix), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(tmp)])


def build_review(tmp, ffmpeg, final, o):
    run([ffmpeg, "-hide_banner", "-y", "-i", str(final), "-c:v", "libx264", "-b:v", o["review_bitrate"],
         "-maxrate", o["review_bitrate"], "-bufsize", "6000k", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(tmp)])


def pick(vdir, stem, kind, lang):
    return next((p for p in (vdir / f"{stem}_{kind}.png", vdir / f"{stem}_{kind}_{lang}.png") if p.exists()), None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    ap.add_argument("--force", default="", help="comma list of layers to rebuild: footage,stills,captions,music,mix,final,review,all")
    a = ap.parse_args()
    kind, lang = a.format, a.lang
    force = {x.strip() for x in a.force.split(",") if x.strip()}
    if "all" in force:
        force = {"footage", "stills", "captions", "music", "mix", "final", "review"}

    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, kind)
    o, au, enh = f_["output"], {**meta["audio"], **f_.get("audio", {})}, meta.get("enhance", {})
    W, H, fps, total = f_["w"], f_["h"], f_["fps"], f_["total"]
    raw = vdir / meta["raw"] if meta.get("raw") else None
    rw, rh = probe_size(raw) if raw else (0, 0)
    cues = parse_srt(vdir / f_["captions"][lang])
    cover, endcard = pick(vdir, "cover", kind, lang), pick(vdir, "endcard", kind, lang)
    if cover is None or endcard is None:
        raise SystemExit("missing cover or end card: run make_cover.py and make_endcard.py first (run_pipeline.py does it)")
    ffmpeg = find_ffmpeg()
    out_dir = OUTPUT_DIR / a.video_id
    L = out_dir / "layers"
    song_src = raw if au["source"] == "raw" else vdir / au["source"]
    voice = None
    if f_["voice"]:
        voice = next((p for p in (vdir / f"voice_{kind}_{lang}.wav", vdir / f"voice_{kind}_tts_{lang}.wav") if p.exists()), None)
        if voice is None:
            raise SystemExit("no voice: run make_voice.py or put voice_<format>_<lang>.wav in the input folder")

    # 1. picture layers
    if raw is None or f_.get("clean_first"):  # cleaned cut, including opted-in single-file products
        footage = L / f"clean_{kind}.mp4"
        if not footage.exists():
            raise SystemExit("no clean cut yet: run cut_rough.py and clean_footage.py first")
        k_footage = digest("footage-from-clean", sig(footage))
    else:
        footage = L / f"footage_{kind}.mp4"
        k_footage = build_cached(footage,
                                 digest("footage", code(build_footage), code(zoom_expr), code(enhance_filters), sig(raw), picture_segments(f_["segments"]),
                                        f_["layout"], W, H, fps, f_["zoom_amount"], enh, rw, rh),
                                 lambda t: build_footage(t, ffmpeg, raw, f_, enh, rw, rh), f"footage_{kind}", "footage" in force)
    stills = {}
    for name, img, dur, zoom in (("cover", cover, f_["cover_dur"], 0.05), ("endcard", endcard, f_["endcard_dur"], 0.04)):
        fade = not (name == "cover" and f_["hook_dur"])  # no dip to black between the hook and the cover
        stills[name] = (L / f"still_{kind}_{lang}_{name}.mp4",
                        digest("still", code(build_still), sig(img), dur, W, H, fps, zoom, fade))
        build_cached(stills[name][0], stills[name][1],
                     lambda t, img=img, dur=dur, zoom=zoom, fade=fade: build_still(t, ffmpeg, img, dur, W, H, fps, zoom, fade),
                     f"still {name}", "stills" in force)
    # 2. captions burned onto the picture
    k_cap = build_cached(L / f"captioned_{kind}_{lang}.mp4",
                         digest("captioned", code(build_captioned), code(write_ass), k_footage, stills["cover"][1], stills["endcard"][1],
                                cues, f_["caption_style"], W, H, fps, o["crf"], f_["hook_dur"]),
                         lambda t: build_captioned(t, ffmpeg, stills["cover"][0], footage, stills["endcard"][0], cues, f_),
                         f"captions {kind} {lang}", "captions" in force)
    # 3. sound layers
    k_music = build_cached(L / f"music_{kind}.wav", digest("music", code(build_music), sig(song_src), au["start"], total),
                           lambda t: build_music(t, ffmpeg, song_src, au, total), f"music {kind}", "music" in force)
    k_mix = build_cached(L / f"mix_{kind}_{lang}.wav",
                         digest("mix", code(build_mix), LOUD, k_music, sig(voice) if voice else "no voice", au["volume"],
                                au["volume_with_voice"], au["fade_out"], total),
                         lambda t: build_mix(t, ffmpeg, L / f"music_{kind}.wav", voice, au, total),
                         f"mix {kind} {lang}" + (f" (voice: {voice.name})" if voice else " (music only)"), "mix" in force)
    # 4. final files
    final = final_dir(a.video_id) / f"{kind}_{lang}.mp4"
    final.parent.mkdir(parents=True, exist_ok=True)
    key_final = digest("final", code(build_final), k_cap, k_mix)
    if final.exists() and (key_of(final) != key_final or "final" in force):
        print("archived the previous final:", archive_old(final).name)  # the old version leaves final/ before the new one goes in
    k_final = build_cached(final, key_final,
                           lambda t: build_final(t, ffmpeg, L / f"captioned_{kind}_{lang}.mp4", L / f"mix_{kind}_{lang}.wav"),
                           f"final {final.name}", "final" in force)
    review = out_dir / "email" / f"{kind}_{lang}_review.mp4"
    build_cached(review, digest("review", code(build_review), k_final, o["review_bitrate"]),
                 lambda t: build_review(t, ffmpeg, final, o), f"review {review.name}", "review" in force)
    print(f"master={final}\nreview={review} ({review.stat().st_size / 1e6:.1f} MB, {total:.1f} s)")


if __name__ == "__main__":
    main()
