"""One command for the whole pipeline (this is what n8n calls).

usage: python run_pipeline.py video-001 --lang en [--voice]
Without --voice: SHORT (captions + music). With --voice: VIDEO (captions + voice-over + music).
Steps: (translate captions if missing) -> cover -> price end card -> (voice) -> edit/render -> prints the output paths as JSON.
Run it with `uv run --with pillow --with imageio-ffmpeg python run_pipeline.py ...` if those are not installed.
"""
import argparse
import json
import subprocess
import sys

from common import ROOT, load_json

HERE = ROOT / "scripts"


def step(*args):
    subprocess.run([sys.executable, *map(str, args)], check=True, cwd=HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--voice", action="store_true")
    a = ap.parse_args()
    kind = "video" if a.voice else "short"
    vdir = ROOT / "input" / a.video_id
    meta = load_json(vdir / "video.json")

    if not (vdir / meta["captions"][a.lang]).exists():
        step("translate_captions.py", a.video_id, "--to", a.lang)
    if not (vdir / "endcard.png").exists():  # a hand-made endcard.png wins over the generated one
        step("make_endcard.py", a.video_id, "--lang", a.lang)
    if not (vdir / "cover.png").exists():
        step("make_cover.py", a.video_id, "--lang", a.lang)
    if a.voice and not (vdir / f"voice_{a.lang}.wav").exists():  # your own recording wins over TTS
        step("make_voice.py", a.video_id, "--lang", a.lang)
    step("edit_short.py", a.video_id, "--lang", a.lang, *(["--voice"] if a.voice else []))

    out = ROOT / "output" / a.video_id
    print(json.dumps({"video_id": a.video_id, "kind": kind, "lang": a.lang, "master": str(out / f"{kind}_{a.lang}.mp4"),
                      "review": str(out / f"{kind}_{a.lang}_review.mp4"), "title": meta["title"][a.lang]}))


if __name__ == "__main__":
    main()
