"""Machine-readable operator commands; the creator can stay in conversation."""

import argparse
import json
from pathlib import Path
import sys
import zipfile

from .models import MechaError, duration, load_json
from .render import doctor, render
from .review import review_packet
from .store import Store


def parser():
    p = argparse.ArgumentParser(description="Mecha assistant-operated episode workspace")
    p.add_argument("--workspace", default=".mecha", help="Durable local workspace path")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check local rendering capabilities without network calls")
    ingest = sub.add_parser("ingest", help="Create or revise a complete episode JSON document")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--note", required=True)
    ingest.add_argument("--expected-revision", type=int)
    for name in ("show", "history", "status"):
        sub.add_parser(name).add_argument("episode")
    feedback = sub.add_parser("feedback")
    feedback.add_argument("episode")
    feedback.add_argument("--text", required=True)
    feedback.add_argument("--expected-revision", type=int, required=True)
    approve = sub.add_parser("approve", help="Record an explicit creator instruction; never self-approve")
    approve.add_argument("episode")
    approve.add_argument("--stage", choices=("script", "storyboard"), required=True)
    approve.add_argument("--note", required=True, help="Exact creator instruction authorizing this stage")
    approve.add_argument("--expected-revision", type=int, required=True)
    audio = sub.add_parser("attach-audio")
    audio.add_argument("episode")
    audio.add_argument("file", type=Path)
    preview = sub.add_parser("render")
    preview.add_argument("episode")
    preview.add_argument("--renderer", choices=("cards", "manim"), default="cards")
    preview.add_argument("--final", action="store_true", help="Require current script/storyboard approvals and narration")
    export = sub.add_parser("export")
    export.add_argument("episode")
    export.add_argument("output", type=Path)
    export.add_argument("--include-audio", action="store_true")
    restore = sub.add_parser("restore")
    restore.add_argument("file", type=Path)
    review = sub.add_parser("review", help="Write a script/storyboard/feedback Markdown packet")
    review.add_argument("episode")
    review.add_argument("output", type=Path)
    return p


def execute(args):
    if args.command == "doctor":
        return doctor()
    store = Store(args.workspace)
    if args.command == "ingest":
        return store.save(load_json(args.file), args.note, args.expected_revision)
    if args.command == "restore":
        return store.restore_bundle(args.file)
    if args.command == "show":
        return store.current(args.episode)
    if args.command == "review":
        return review_packet(store, args.episode, args.output)
    if args.command == "history":
        return store.history(args.episode)
    if args.command == "status":
        current = store.current(args.episode)
        return {"id": args.episode, "revision": current["revision"], "hash": current["hash"],
                "duration_seconds": duration(current["document"]), "approvals": store.approvals(args.episode, current["revision"]),
                "audio": {k: v for k, v in (store.get_audio(args.episode) or {}).items() if k != "path"}}
    if args.command == "feedback":
        store.feedback(args.episode, args.text, args.expected_revision)
        return {"recorded": True}
    if args.command == "approve":
        store.approve(args.episode, args.stage, args.note, args.expected_revision)
        return {"recorded": True, "stage": args.stage, "revision": args.expected_revision}
    if args.command == "attach-audio":
        return store.attach_audio(args.episode, args.file)
    if args.command == "render":
        return render(store, args.episode, args.renderer, args.final)
    if args.command == "export":
        return store.export_bundle(args.episode, args.output, args.include_audio)
    raise MechaError("Unknown command")


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = execute(args)
    except (MechaError, OSError, zipfile.BadZipFile, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
