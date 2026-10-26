"""Translate captions_en.srt into another language with an LLM, keeping the timings.

usage: python translate_captions.py video-001 --to es [--provider anthropic|openai]
Writes input/<id>/captions_<lang>.srt. Existing files are kept unless --force.
"""
import argparse
import json

from common import ROOT, load_json, parse_srt, write_srt
from llm_client import complete

LANGS = {"es": "Spanish (Spain)", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--to", required=True)
    ap.add_argument("--provider")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    vdir = ROOT / "input" / a.video_id
    out = vdir / f"captions_{a.to}.srt"
    if out.exists() and not a.force:
        print("exists, keeping", out)
        return
    meta = load_json(vdir / "video.json")
    cues = parse_srt(vdir / meta["captions"]["en"])
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
