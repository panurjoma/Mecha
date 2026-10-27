"""Run the four reviewer agents (.claude/agents/*.md) on a finished short or video through an LLM, for use in n8n.

usage: python review_video.py <video-id> --format short|video --lang en
Needs ANTHROPIC_API_KEY or OPENAI_API_KEY in .env. Runs review_pack.py first, then sends each role's instructions with the
facts file and the contact sheets (images only with Claude) and writes <OUTPUT_DIR>/<id>/review/<format>_<lang>_review.md.
Language: agents marked `language: separate` are run for each language (en, es), `shared` ones once on the first language,
`separate-if-voice` ones per language only when the product has a voice-over (see .claude/agents). Without a key it says so and exits without a review. In Claude Code the same roles can be run as parallel agents instead.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from common import OUTPUT_DIR, ROOT
from llm_client import complete, pick_provider


def language_mode(agent_text):
    """The agent's `language:` setting from its frontmatter: separate, shared or separate-if-voice."""
    m = re.search(r"^language:\s*(\S+)", agent_text.split("---")[1], re.M)
    return m.group(1) if m else "separate"


def langs_for(mode, has_voice, langs):
    """Languages an agent must be run for: all of them if its judgment depends on language, else only the first."""
    return langs if mode == "separate" or (mode == "separate-if-voice" and has_voice) else langs[:1]


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
    for role in sorted((ROOT / ".claude" / "agents").glob("*.md")):
        head, body = role.read_text(encoding="utf-8").split("---", 2)[1:]  # frontmatter, then the instructions
        body = body.strip()
        model = next((ln.split(":", 1)[1].strip() for ln in head.splitlines() if ln.startswith("model:")), None)
        text = complete(f"Evidence for the {a.format} ({a.lang}):\n\n{facts}\n\nThe contact sheets are attached (one frame per "
                        "second, time-stamped). Keep the answer under 350 words.", system=body,
                        max_tokens=1200, model=model, images=sheets + sorted(pack.glob("sources_sheet_*.jpg")))
        parts.append(f"## {role.stem}\n\n{text.strip()}\n")
    out = pack / f"{a.format}_{a.lang}_review.md"
    out.write_text(f"# Critic review: {a.video_id} {a.format} {a.lang}\n\n" + "\n".join(parts), encoding="utf-8")
    print(f"review={out}")


if __name__ == "__main__":
    main()
