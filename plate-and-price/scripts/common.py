"""Shared helpers: paths, ffmpeg lookup, .env loading, SRT parsing."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
