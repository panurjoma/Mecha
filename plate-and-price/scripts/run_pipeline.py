"""One command for the whole pipeline (this is what n8n calls).

usage: python run_pipeline.py <video-id> --format short|video --lang en
  short: captions + music, 1080x1920 for YouTube Shorts.
  video: captions + voice-over + music, 1920x1080 for the YouTube channel.
Every video layer is cached (see layers.py): only the layers whose inputs changed are rebuilt; --force rebuilds chosen ones.
Steps: translate captions if missing -> AI cover check -> cover -> price end card -> (voice) -> edit/render -> YouTube
title, description and tags (description_<format>_<lang>.md). Prints one JSON line with the output paths and the text. Run it with
`uv run --with pillow --with imageio-ffmpeg --with edge-tts python run_pipeline.py ...` if those are not installed.
"""
import argparse
import json
import subprocess
import sys

from common import OUTPUT_DIR, ROOT, fmt, load_json, video_dir

HERE = ROOT / "scripts"


def step(*args, check=True):
    return subprocess.run([sys.executable, *map(str, args)], check=check, cwd=HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    ap.add_argument("--force", default="", help="layers to rebuild even if unchanged: footage,stills,captions,voice,music,mix,final,review,all")
    a = ap.parse_args()
    force = {x.strip() for x in a.force.split(",") if x.strip()}
    kind = a.format
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, kind)

    if not (vdir / f_["captions"][a.lang]).exists():
        step("translate_captions.py", a.video_id, "--format", kind, "--to", a.lang)
    step("make_cover_ai.py", a.video_id, check=False)  # only reports when an AI cover image is missing
    if not (vdir / f"cover_{kind}.png").exists():  # a hand-made cover_<format>.png wins over the generated one
        step("make_cover.py", a.video_id, "--format", kind, "--lang", a.lang)
    if not (vdir / f"endcard_{kind}.png").exists():
        step("make_endcard.py", a.video_id, "--format", kind, "--lang", a.lang)
    if f_["voice"] and not (vdir / f"voice_{kind}_{a.lang}.wav").exists():  # your own recording wins over TTS
        step("make_voice.py", a.video_id, "--format", kind, "--lang", a.lang, *(["--force"] if force & {"voice", "all"} else []))
    step("edit_short.py", a.video_id, "--format", kind, "--lang", a.lang, *(["--force", ",".join(force - {"voice"})] if force - {"voice"} else []))

    from make_description import build  # after the render so a description problem never loses the video
    desc_file, yt_title, yt_body = build(a.video_id, kind, a.lang)
    out = OUTPUT_DIR / a.video_id
    print(json.dumps({"video_id": a.video_id, "format": kind, "lang": a.lang, "master": str(out / f"{kind}_{a.lang}.mp4"),
                      "review": str(out / f"{kind}_{a.lang}_review.mp4"), "title": meta["title"][a.lang],
                      "youtube_title": yt_title, "description_file": str(desc_file), "description": yt_body}))


if __name__ == "__main__":
    main()
