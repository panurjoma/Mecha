"""Shared helpers: paths, ffmpeg lookup, .env loading, SRT parsing, per-format settings."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # .../plate-and-price (the folder inside the git repo)


def load_env():
    """Read ROOT/.env (KEY=value lines) into os.environ without overriding real env vars."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
# Rendered videos are not part of the repo: set PLATE_OUTPUT_DIR in .env to keep them elsewhere.
OUTPUT_DIR = Path(os.environ.get("PLATE_OUTPUT_DIR") or ROOT / "output")


def final_dir(video_id):
    """<OUTPUT_DIR>/<id>/final: the approved short and video files, descriptions and thumbnails of a recipe (directive 23)."""
    return OUTPUT_DIR / video_id / "final"


def archive_old(path):
    """Move a final file (and its .key sidecar) out of final/ into ../archive/ with a time stamp before it is replaced."""
    import time
    path = Path(path)
    if not path.exists():
        return None
    arch = path.parent.parent / "archive"
    arch.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(path.stat().st_mtime))
    dest = arch / f"{path.stem}_{stamp}{path.suffix}"
    path.replace(dest)
    side = Path(str(path) + ".key")
    if side.exists():
        side.replace(Path(str(dest) + ".key"))
    return dest


def find_ffmpeg():
    """FFMPEG env var, then PATH, then the imageio-ffmpeg wheel (uv run --with imageio-ffmpeg)."""
    if os.environ.get("FFMPEG"):
        return os.environ["FFMPEG"]
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found: install it, set FFMPEG, or run with `uv run --with imageio-ffmpeg`")


def run(cmd, cwd=None):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def video_dir(video_id):
    return ROOT / "input" / video_id


def fmt(meta, kind):
    """Settings of one product ('short' or 'video'): output size, layout, segments, captions, style, durations."""
    f = dict(meta["formats"][kind])
    f["kind"] = kind
    f["w"], f["h"] = f["output"]["width"], f["output"]["height"]
    f["fps"] = f["output"]["fps"]
    f["total"] = f["cover_dur"] + sum(s["dur"] for s in f["segments"]) + f["endcard_dur"]
    # an optional moving hook: the first segment, flagged "hook": true, is shown before the cover card
    f["hook_dur"] = f["segments"][0]["dur"] if f["segments"] and f["segments"][0].get("hook") else 0
    return f


def probe_size(path):
    """(width, height) of the first video stream, read from ffmpeg's banner."""
    err = subprocess.run([find_ffmpeg(), "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Video:.*?, (\d{2,5})x(\d{2,5})", err)
    return int(m.group(1)), int(m.group(2))


def find_font(bold=True):
    names = (["arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"] if bold
             else ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"])
    dirs = [os.environ.get("FONT_DIR", ""), r"C:\Windows\Fonts", "/usr/share/fonts/truetype/dejavu",
            "/Library/Fonts", "/System/Library/Fonts/Supplemental"]
    for d in dirs:
        for n in names:
            p = Path(d) / n
            if d and p.exists():
                return str(p)
    raise SystemExit("no usable font found: set FONT_DIR")


_TS = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)")


def _secs(ts):
    h, m, s, ms = _TS.match(ts.strip()).groups()
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def parse_srt(path):
    """Return [(start_s, end_s, text_with_\\n)]."""
    out = []
    for block in re.split(r"\n\s*\n", Path(path).read_text(encoding="utf-8-sig").strip()):
        lines = block.strip().splitlines()
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        a, b = lines[1].split("-->")
        out.append((_secs(a), _secs(b), "\n".join(lines[2:])))
    return out


def write_srt(path, cues):
    def ts(t):
        ms = round(t * 1000)
        return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    body = "\n\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}" for i, (a, b, t) in enumerate(cues, 1))
    Path(path).write_text(body + "\n", encoding="utf-8")
