"""SQLite is authoritative; portable bundles carry immutable revision history."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import zipfile

from .models import MechaError, canonical, digest, identifier, text, validate


def now():
    return datetime.now(timezone.utc).isoformat()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "audio").mkdir(exist_ok=True)
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS episodes(id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS revisions(
                    episode TEXT REFERENCES episodes(id), revision INTEGER,
                    hash TEXT, document TEXT, note TEXT, created_at TEXT,
                    PRIMARY KEY(episode, revision));
                CREATE TABLE IF NOT EXISTS events(
                    id INTEGER PRIMARY KEY, episode TEXT REFERENCES episodes(id),
                    revision INTEGER, kind TEXT, payload TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS audio(
                    episode TEXT PRIMARY KEY REFERENCES episodes(id),
                    hash TEXT, seconds REAL, name TEXT);
                CREATE TABLE IF NOT EXISTS renders(
                    episode TEXT REFERENCES episodes(id), revision INTEGER,
                    key TEXT, manifest TEXT, created_at TEXT);
            """)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.root / "mecha.sqlite3", timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def current(self, episode):
        identifier(episode)
        with self.db() as db:
            row = db.execute("SELECT * FROM revisions WHERE episode=? ORDER BY revision DESC LIMIT 1", (episode,)).fetchone()
        if row is None:
            raise MechaError(f"Unknown episode: {episode}")
        return dict(row) | {"document": json.loads(row["document"])}

    def save(self, doc, note, expected_revision=None):
        validate(doc)
        text(note, "revision note", 2000)
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT revision,hash FROM revisions WHERE episode=? ORDER BY revision DESC LIMIT 1", (doc["id"],)).fetchone()
            revision = row["revision"] if row else 0
            if expected_revision is not None and revision != expected_revision:
                raise MechaError(f"Revision conflict: expected {expected_revision}, current {revision}")
            if row and expected_revision is None:
                raise MechaError("Updates require --expected-revision to avoid overwriting corrections")
            if row and row["hash"] == digest(doc):
                return {"id": doc["id"], "revision": revision, "changed": False}
            db.execute("INSERT OR IGNORE INTO episodes VALUES(?)", (doc["id"],))
            db.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?)", (doc["id"], revision + 1, digest(doc), canonical(doc), note, now()))
        return {"id": doc["id"], "revision": revision + 1, "changed": True}

    def event(self, episode, kind, payload, revision):
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT MAX(revision) FROM revisions WHERE episode=?", (episode,)).fetchone()
            if row[0] != revision:
                raise MechaError("Revision changed; reread the episode before recording feedback/approval")
            db.execute("INSERT INTO events(episode,revision,kind,payload,created_at) VALUES(?,?,?,?,?)", (episode, revision, kind, canonical(payload), now()))

    def feedback(self, episode, message, expected_revision):
        text(message, "feedback", 6000)
        self.event(episode, "feedback", {"text": message}, expected_revision)

    def approve(self, episode, stage, note, expected_revision):
        if stage not in ("script", "storyboard"):
            raise MechaError("Approval stage must be script or storyboard")
        text(note, "approval evidence", 2000)
        self.event(episode, "approval", {"stage": stage, "creator_instruction": note}, expected_revision)

    def history(self, episode):
        self.current(episode)
        with self.db() as db:
            revisions = [dict(r) for r in db.execute("SELECT * FROM revisions WHERE episode=? ORDER BY revision", (episode,))]
            events = [dict(r) for r in db.execute("SELECT * FROM events WHERE episode=? ORDER BY id", (episode,))]
        for r in revisions:
            r["document"] = json.loads(r["document"])
        for e in events:
            e["payload"] = json.loads(e["payload"])
            del e["id"]
        return {"revisions": revisions, "events": events}

    def approvals(self, episode, revision):
        history = self.history(episode)
        return sorted({e["payload"]["stage"] for e in history["events"] if e["revision"] == revision and e["kind"] == "approval"})

    def attach_audio(self, episode, source):
        self.current(episode)
        from .render import probe_audio
        source = Path(source).resolve()
        if not source.is_file() or source.stat().st_size > 250_000_000:
            raise MechaError("Audio must be a local file no larger than 250 MB")
        h = file_hash(source)
        seconds = probe_audio(source)
        destination = self.root / "audio" / h
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as tmp:
            temporary = Path(tmp.name)
        try:
            shutil.copyfile(source, temporary)
            if file_hash(temporary) != h:
                raise MechaError("Audio changed while importing; retry with a stable file")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO audio VALUES(?,?,?,?)", (episode, h, seconds, source.name))
        return {"hash": h, "seconds": seconds, "name": source.name}

    def get_audio(self, episode):
        with self.db() as db:
            row = db.execute("SELECT * FROM audio WHERE episode=?", (episode,)).fetchone()
        if not row:
            return None
        data = dict(row)
        path = self.root / "audio" / data["hash"]
        if not path.is_file() or file_hash(path) != data["hash"]:
            raise MechaError("Stored narration is missing or corrupt; restore the complete project bundle")
        return data | {"path": str(path)}

    def export_bundle(self, episode, output, include_audio=False):
        data = {"bundle_version": 1, "episode": episode, **self.history(episode), "audio": None}
        audio = self.get_audio(episode)
        if audio and include_audio:
            data["audio"] = {k: audio[k] for k in ("hash", "seconds", "name")}
        output = Path(output).resolve()
        if output.exists():
            raise MechaError("Export destination already exists; choose a new versioned filename")
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip", delete=False) as tmp:
            temp = Path(tmp.name)
        try:
            with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("project.json", canonical(data))
                if data["audio"]:
                    z.write(audio["path"], "audio/" + audio["hash"])
            temp.replace(output)
        finally:
            temp.unlink(missing_ok=True)
        return {"path": str(output), "revision": self.current(episode)["revision"], "includes_audio": bool(data["audio"])}

    def restore_bundle(self, path):
        from .models import keys
        with zipfile.ZipFile(path) as z:
            if len(z.namelist()) != len(set(z.namelist())) or len(z.namelist()) > 2:
                raise MechaError("Unexpected or duplicate bundle entries")
            if sum(i.file_size for i in z.infolist()) > 260_000_000:
                raise MechaError("Bundle is too large")
            if "project.json" not in z.namelist() or z.getinfo("project.json").file_size > 5_000_000:
                raise MechaError("Missing or oversized project.json")
            data = json.loads(z.read("project.json"))
            keys(data, ("bundle_version", "episode", "revisions", "events", "audio"))
            if data["bundle_version"] != 1 or not data["revisions"]:
                raise MechaError("Unsupported or empty bundle")
            episode = identifier(data["episode"])
            for index, r in enumerate(data["revisions"], 1):
                keys(r, ("episode", "revision", "hash", "document", "note", "created_at"))
                validate(r["document"])
                if r["episode"] != episode or r["document"]["id"] != episode or type(r["revision"]) is not int or r["revision"] != index or r["hash"] != digest(r["document"]):
                    raise MechaError("Invalid revision chain or content hash")
                text(r["note"], "revision note", 2000)
                text(r["created_at"], "timestamp", 100)
            for e in data["events"]:
                keys(e, ("episode", "revision", "kind", "payload", "created_at"))
                if e["episode"] != episode or type(e["revision"]) is not int or not 1 <= e["revision"] <= len(data["revisions"]):
                    raise MechaError("Invalid event revision")
                if e["kind"] == "feedback":
                    keys(e["payload"], ("text",))
                    text(e["payload"]["text"], "feedback", 6000)
                elif e["kind"] == "approval":
                    keys(e["payload"], ("stage", "creator_instruction"))
                    if e["payload"]["stage"] not in ("script", "storyboard"):
                        raise MechaError("Invalid approval")
                    text(e["payload"]["creator_instruction"], "approval evidence", 2000)
                else:
                    raise MechaError("Unknown event kind")
                text(e["created_at"], "timestamp", 100)
            audio = data["audio"]
            expected_names = {"project.json"}
            if audio:
                keys(audio, ("hash", "seconds", "name"))
                import re
                if not isinstance(audio["hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", audio["hash"]):
                    raise MechaError("Invalid audio hash")
                expected_names.add("audio/" + audio["hash"])
            if set(z.namelist()) != expected_names:
                raise MechaError("Unexpected bundle paths")
            audio_bytes = z.read("audio/" + audio["hash"]) if audio else None
            if audio and hashlib.sha256(audio_bytes).hexdigest() != audio["hash"]:
                raise MechaError("Narration checksum mismatch")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM episodes WHERE id=?", (episode,)).fetchone():
                raise MechaError("Episode already exists; restore into a fresh workspace to compare")
            if audio:
                from .render import probe_audio
                with tempfile.NamedTemporaryFile(dir=self.root / "audio", delete=False) as tmp:
                    tmp.write(audio_bytes)
                    temp = Path(tmp.name)
                try:
                    seconds = probe_audio(temp)
                    text(audio["name"], "audio name", 255)
                    audio["seconds"] = seconds
                    temp.replace(self.root / "audio" / audio["hash"])
                finally:
                    temp.unlink(missing_ok=True)
            db.execute("INSERT INTO episodes VALUES(?)", (episode,))
            for r in data["revisions"]:
                db.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?)", (episode, r["revision"], r["hash"], canonical(r["document"]), r["note"], r["created_at"]))
            for e in data["events"]:
                db.execute("INSERT INTO events(episode,revision,kind,payload,created_at) VALUES(?,?,?,?,?)", (episode, e["revision"], e["kind"], canonical(e["payload"]), e["created_at"]))
            if audio:
                db.execute("INSERT INTO audio VALUES(?,?,?,?)", (episode, audio["hash"], audio["seconds"], audio["name"]))
        return {"id": episode, "revision": len(data["revisions"]), "includes_audio": bool(audio)}
