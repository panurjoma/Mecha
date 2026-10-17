"""Human-readable review packets generated from authoritative workspace state."""

from pathlib import Path

from .models import MechaError, duration


def review_packet(store, episode, output):
    current = store.current(episode)
    doc = current["document"]
    lines = [f"# {doc['topic']}", "", f"Episode: {episode} · Revision: {current['revision']}",
             f"Audience: {doc['audience']} · Locale: {doc['locale']} · Duration: {duration(doc):g}s", "",
             "## Storytelling", "", doc["storytelling"], "", "## Script and storyboard", ""]
    start = 0
    for scene in doc["scenes"]:
        end = start + scene["duration_seconds"]
        lines += [f"### {start:g}–{end:g}s · {scene['title']}", "", "Narration:", "", scene["narration"], "",
                  f"Visual ({scene['visual']['kind']}): {scene['visual']['caption']}", ""]
        for claim in scene["claims"]:
            lines += [f"- Claim: {claim['text']} (sources: {', '.join(claim['source_ids'])})"]
        lines += [""]
        start = end
    lines += ["## Sources", ""]
    lines += [f"- {s['id']}: {s['title']} — {s['url']}" for s in doc["sources"]]
    lines += ["", "## Feedback history", ""]
    for event in store.history(episode)["events"]:
        message = event["payload"].get("text", event["payload"].get("creator_instruction", ""))
        lines += [f"- Revision {event['revision']} · {event['kind']}: {message}"]
    approvals = store.approvals(episode, current["revision"])
    lines += ["", "Current approvals: " + (", ".join(approvals) if approvals else "none"),
              "", "This packet is a review view. Restore/export the project bundle to preserve editable history.", ""]
    output = Path(output)
    if output.exists():
        raise MechaError("Review destination exists; use a revision-specific filename")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return {"path": str(output.resolve()), "revision": current["revision"]}
