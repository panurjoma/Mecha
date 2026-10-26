"""Translate captions_en.srt into another language with an LLM, keeping the timings.

usage: python translate_captions.py <video-id> --format short|video --to es [--provider anthropic|openai]
Translates formats.<format>.captions.en into captions.<lang> (file name from video.json), keeping timings.
Existing files are kept unless --force.
"""
import argparse
import json

from common import fmt, load_json, parse_srt, video_dir, write_srt
from llm_client import complete

LANGS = {"es": "Spanish (Spain)", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--to", required=True)
    ap.add_argument("--provider")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, a.format)
    out = vdir / f_["captions"].get(a.to, f"captions_{a.format}_{a.to}.srt")
    if out.exists() and not a.force:
        print("exists, keeping", out)
        return
    cues = parse_srt(vdir / f_["captions"]["en"])
    texts = [t for _, _, t in cues]
    reply = complete(
        f"Translate these on-screen cooking captions into {LANGS.get(a.to, a.to)}. Keep each caption short, natural and "
        "casual, keep the line breaks (\\n), keep food names accurate. Return ONLY a JSON array of strings, same length "
        f"({len(texts)}) and order.\n\n" + json.dumps(texts, ensure_ascii=False),
        system="You are a professional subtitle translator for short cooking videos.", provider=a.provider)
    start, end = reply.find("["), reply.rfind("]") + 1
    new = json.loads(reply[start:end])
    if len(new) != len(cues):
        raise SystemExit(f"LLM returned {len(new)} captions, expected {len(cues)}")
    write_srt(out, [(s, e, t) for (s, e, _), t in zip(cues, new)])
    print("wrote", out)


if __name__ == "__main__":
    main()
