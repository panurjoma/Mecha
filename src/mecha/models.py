"""Small, strict JSON contracts. No generated Python is ever evaluated."""

import hashlib
import json
import math
import re
from urllib.parse import urlparse


class MechaError(ValueError):
    """An actionable input or workflow error."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def keys(value, required, optional=()):
    if not isinstance(value, dict):
        raise MechaError("Expected a JSON object")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise MechaError(f"Invalid fields: missing={sorted(missing)}, unknown={sorted(extra)}")


def text(value, label, limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise MechaError(f"{label} must be nonempty text, at most {limit} characters")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise MechaError(f"{label} contains control characters")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value):
        raise MechaError("IDs must contain 1–64 lowercase letters, digits or hyphens")
    return value


def number(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MechaError(f"{label} must be a number")
    if not math.isfinite(value) or not low <= value <= high:
        raise MechaError(f"{label} must be between {low} and {high}")


def validate(doc):
    keys(doc, ("schema_version", "id", "topic", "audience", "locale", "storytelling", "sources", "scenes"))
    if type(doc["schema_version"]) is not int or doc["schema_version"] != 1:
        raise MechaError("Only schema_version 1 is supported")
    identifier(doc["id"])
    text(doc["topic"], "topic", 200)
    text(doc["audience"], "audience", 300)
    if doc["locale"] != "es-ES":
        raise MechaError("The first version supports es-ES")
    text(doc["storytelling"], "storytelling", 6000)
    if not isinstance(doc["sources"], list) or len(doc["sources"]) > 100:
        raise MechaError("sources must be a list of at most 100 entries")
    source_ids = set()
    for source in doc["sources"]:
        keys(source, ("id", "title", "url"))
        sid = identifier(source["id"])
        if sid in source_ids:
            raise MechaError("Duplicate source ID")
        source_ids.add(sid)
        text(source["title"], "source title", 300)
        text(source["url"], "source URL", 2000)
        parsed = urlparse(source["url"])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise MechaError("Sources require HTTPS URLs without credentials")
    if not isinstance(doc["scenes"], list) or not 1 <= len(doc["scenes"]) <= 100:
        raise MechaError("Provide 1–100 scenes")
    scene_ids = set()
    for scene in doc["scenes"]:
        keys(scene, ("id", "title", "narration", "duration_seconds", "visual", "claims"))
        sid = identifier(scene["id"])
        if sid in scene_ids:
            raise MechaError("Duplicate scene ID")
        scene_ids.add(sid)
        text(scene["title"], "scene title", 100)
        text(scene["narration"], "narration", 3000)
        number(scene["duration_seconds"], "scene duration", 1, 120)
        visual = scene["visual"]
        keys(visual, ("kind", "caption"), ("turns",))
        if visual["kind"] not in ("card", "orbit"):
            raise MechaError("visual.kind must be card or orbit")
        text(visual["caption"], "visual caption", 300)
        if "turns" in visual:
            if visual["kind"] != "orbit":
                raise MechaError("turns only applies to orbit scenes")
            number(visual["turns"], "orbit turns", 0.1, 5)
        if not isinstance(scene["claims"], list) or len(scene["claims"]) > 30:
            raise MechaError("claims must be a list with at most 30 entries")
        for claim in scene["claims"]:
            keys(claim, ("text", "source_ids"))
            text(claim["text"], "claim", 1000)
            if not isinstance(claim["source_ids"], list) or not claim["source_ids"]:
                raise MechaError("Each claim requires source_ids")
            if any(not isinstance(s, str) or s not in source_ids for s in claim["source_ids"]):
                raise MechaError("Claim references an unknown source")
    if duration(doc) > 1800:
        raise MechaError("Episode exceeds the 30-minute pilot limit")
    return doc


def duration(doc):
    return sum(scene["duration_seconds"] for scene in doc["scenes"])


def load_json(path):
    try:
        with open(path, encoding="utf-8") as stream:
            if len(data := stream.read(2_000_001)) > 2_000_000:
                raise MechaError("JSON input exceeds 2 MB")
        return json.loads(data)
    except (OSError, json.JSONDecodeError) as exc:
        raise MechaError(f"Cannot read JSON: {exc}") from exc
