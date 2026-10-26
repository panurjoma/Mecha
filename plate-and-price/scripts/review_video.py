"""Run the reviewer roles (review/roles/*.md) on a finished short or video through an LLM, for use in n8n.

usage: python review_video.py <video-id> --format short|video --lang en
Needs ANTHROPIC_API_KEY or OPENAI_API_KEY in .env. Runs review_pack.py first, then sends each role's instructions with the
facts file and the contact sheets (images only with Claude) and writes <OUTPUT_DIR>/<id>/review/<format>_<lang>_review.md.
Without a key it says so and exits without a review. In Claude Code the same roles can be run as parallel agents instead.
"""
import argparse
import subprocess
import sys
from pathlib import Path

from common import OUTPUT_DIR, ROOT
from llm_client import complete, pick_provider


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    try:
        pick_provider()
    except RuntimeError as e:
        raise SystemExit(f"review skipped: {e}")
    subprocess.run([sys.executable, str(Path(__file__).with_name("review_pack.py")), a.video_id, "--format", a.format,
                    "--lang", a.lang], check=True)
    pack = OUTPUT_DIR / a.video_id / "review"
    facts = (pack / f"{a.format}_{a.lang}_facts.md").read_text(encoding="utf-8")
    sheets = sorted(pack.glob(f"{a.format}_{a.lang}_sheet_*.jpg"))
    parts = []
    for role in sorted((ROOT / "review" / "roles").glob("*.md")):
        text = complete(f"Evidence for the {a.format} ({a.lang}):\n\n{facts}\n\nThe contact sheets are attached (one frame per "
                        "second, time-stamped). Keep the answer under 350 words.", system=role.read_text(encoding="utf-8"),
                        max_tokens=1200, images=sheets)
        parts.append(f"## {role.stem}\n\n{text.strip()}\n")
    out = pack / f"{a.format}_{a.lang}_review.md"
    out.write_text(f"# Critic review: {a.video_id} {a.format} {a.lang}\n\n" + "\n".join(parts), encoding="utf-8")
    print(f"review={out}")


if __name__ == "__main__":
    main()
