"""Layer cache: build each layer file once and rebuild it only when its own inputs change.

A layer is a file plus a small sidecar `<file>.key` holding a fingerprint of everything the layer depends on (input
files by content, settings, and the source code of the function that builds it). If the fingerprint matches, the
layer is reused ("cached"); otherwise it is rebuilt ("built") and everything that depends on it rebuilds too,
because their fingerprints include this layer's.
"""
import hashlib
import inspect
import json
from pathlib import Path


def sig(path):
    """Fingerprint of a file by content ('missing' if absent)."""
    p = Path(path)
    if not p.exists():
        return "missing"
    h = hashlib.sha1()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def code(fn):
    """Fingerprint of a function's source, so editing the build code invalidates its layer."""
    return hashlib.sha1(inspect.getsource(fn).encode()).hexdigest()[:8]


def digest(*parts):
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def key_of(path):
    side = Path(str(path) + ".key")
    return side.read_text().strip() if side.exists() else None


def build_cached(path, key, builder, label, force=False):
    """Run builder(tmp_path) to create `path` unless it exists with the same key. Returns the layer's key."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not force and path.exists() and key_of(path) == key:
        print(f"[cached] {label}", flush=True)
        return key
    tmp = path.with_name(path.stem + ".tmp" + path.suffix)
    builder(tmp)
    tmp.replace(path)
    Path(str(path) + ".key").write_text(key)
    print(f"[built]  {label}", flush=True)
    return key
