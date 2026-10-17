"""Bounded, shell-free rendering from fixed templates and validated data."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap

from .models import MechaError, canonical, digest, duration
from .store import file_hash, now

TEMPLATE_VERSION = "1"


def run(args, timeout=180):
    try:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MechaError(f"Media command failed: {exc}") from exc
    if result.returncode:
        raise MechaError(f"{Path(args[0]).name} failed: {result.stderr[-2000:]}")
    return result.stdout


def require(name):
    if not shutil.which(name):
        raise MechaError(f"Missing {name}; run mecha doctor and follow docs/ASSISTANT_WORKFLOW.md")


def probe(path):
    require("ffprobe")
    return json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]))


def probe_audio(path):
    data = probe(path)
    if not any(s["codec_type"] == "audio" for s in data["streams"]):
        raise MechaError("Narration file contains no audio stream")
    try:
        seconds = float(data["format"]["duration"])
    except (KeyError, ValueError) as exc:
        raise MechaError("Cannot determine narration duration") from exc
    if not 0 < seconds <= 1800:
        raise MechaError("Narration must be between 0 and 1800 seconds")
    return seconds


def doctor():
    return {"python": sys.version.split()[0], "ffmpeg": bool(shutil.which("ffmpeg")),
            "ffprobe": bool(shutil.which("ffprobe")), "manim": importlib.util.find_spec("manim") is not None,
            "blender": bool(shutil.which("blender")),
            "note": "Cards need FFmpeg with drawtext and DejaVu Sans. Manim is optional; Blender is not implemented in v0.1."}


def timestamp(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    sec, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{sec:02},{ms:03}"


def subtitles(doc):
    cues, start = [], 0
    for index, scene in enumerate(doc["scenes"], 1):
        end = start + scene["duration_seconds"]
        cues.append(f"{index}\n{timestamp(start)} --> {timestamp(end)}\n{scene['narration']}\n")
        start = end
    return "\n".join(cues)


def render_card(scene, output, work):
    # Only fixed relative filenames enter the filter expression; text is never filter syntax.
    (work / "title.txt").write_text("\n".join(textwrap.wrap(scene["title"], 44)), encoding="utf-8")
    caption = scene["visual"]["caption"]
    if scene["visual"]["kind"] == "orbit":
        caption += "\n[Storyboard: animación orbital pendiente en Manim]"
    (work / "caption.txt").write_text("\n".join(textwrap.wrap(caption, 62)), encoding="utf-8")
    (work / "label.txt").write_text("MECHA · BORRADOR DE STORYBOARD", encoding="utf-8")
    vf = ("drawtext=font=DejaVuSans:textfile=title.txt:expansion=none:fontcolor=white:fontsize=28:x=(w-tw)/2:y=55,"
          "drawtext=font=DejaVuSans:textfile=caption.txt:expansion=none:fontcolor=0xA7CEF5:fontsize=20:x=(w-tw)/2:y=160,"
          "drawtext=font=DejaVuSans:textfile=label.txt:expansion=none:fontcolor=0x8BA0B6:fontsize=14:x=(w-tw)/2:y=h-38")
    # cwd is a generated temporary directory; source/output paths are absolute.
    args = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-threads", "1", "-filter_threads", "1",
            "-f", "lavfi", "-i", "color=c=0x101C2D:s=854x480:r=15", "-t", str(scene["duration_seconds"]),
            "-vf", vf, "-an", "-c:v", "libx264", "-threads", "1", "-pix_fmt", "yuv420p", str(output)]
    try:
        result = subprocess.run(args, cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MechaError(f"Card render failed: {exc}") from exc
    if result.returncode:
        raise MechaError(f"Card render failed: {result.stderr[-2000:]}")


def render_manim(scene, output, work):
    if importlib.util.find_spec("manim") is None:
        raise MechaError("Manim not installed. Install mecha-video[animation] or use --renderer cards for a labeled storyboard")
    spec = work / "scene.json"
    spec.write_text(canonical(scene), encoding="utf-8")
    env = dict(os.environ, MECHA_SCENE_SPEC=str(spec))
    args = [sys.executable, "-m", "manim", "render", "--renderer", "cairo", "-ql", "--disable_caching",
            "--media_dir", str(work / "media"), "-o", "scene.mp4", str(Path(__file__).with_name("manim_scene.py")), "EpisodeScene"]
    try:
        result = subprocess.run(args, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MechaError(f"Manim failed: {exc}") from exc
    if result.returncode:
        raise MechaError(f"Manim failed: {result.stderr[-2000:]}")
    files = list((work / "media" / "videos").glob("**/scene.mp4"))
    if len(files) != 1:
        raise MechaError("Manim did not produce exactly one scene.mp4")
    # Normalize output so clips from both renderers share one muxing contract.
    run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(files[0]), "-vf", "scale=854:480,fps=15",
         "-an", "-c:v", "libx264", "-threads", "1", "-pix_fmt", "yuv420p", str(output)])


def render(store, episode, renderer="cards", final=False):
    require("ffmpeg")
    require("ffprobe")
    if renderer not in ("cards", "manim"):
        raise MechaError("Unknown renderer")
    current = store.current(episode)
    doc, revision = current["document"], current["revision"]
    audio = store.get_audio(episode)
    seconds = duration(doc)
    if final:
        if renderer != "manim":
            raise MechaError("Final proof requires Manim; cards are only a storyboard preview")
        if set(store.approvals(episode, revision)) != {"script", "storyboard"}:
            raise MechaError("Current revision needs explicit creator script and storyboard approvals")
        if not audio:
            raise MechaError("Attach your recorded narration before a final proof")
    if audio and abs(audio["seconds"] - seconds) > 0.5:
        raise MechaError(f"Narration is {audio['seconds']:.2f}s, storyboard is {seconds:.2f}s; revise scene durations to match within 0.5s")
    # Audio attachment changes and template changes invalidate reuse.
    key = digest({"document": current["hash"], "revision": revision, "renderer": renderer, "final": final,
                  "audio": audio["hash"] if audio else None, "template": TEMPLATE_VERSION})
    dest = store.root / "renders" / episode / key
    manifest_path = dest / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        if all((dest / name).is_file() and file_hash(dest / name) == h for name, h in manifest["files"].items()):
            # Approval remains checked above even when final output is cached.
            return manifest | {"cached": True, "directory": str(dest)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
        work = Path(tmp)
        clips = []
        for index, scene in enumerate(doc["scenes"]):
            scene_work = work / f"scene-{index}"
            scene_work.mkdir()
            clip = scene_work / "clip.mp4"
            clip_key = digest({"scene": scene, "renderer": renderer, "template": TEMPLATE_VERSION})
            cache = store.root / "clip-cache"
            cache.mkdir(exist_ok=True)
            cached_clip = cache / f"{clip_key}.mp4"
            cached_hash = cache / f"{clip_key}.sha256"
            if cached_clip.is_file() and cached_hash.is_file() and file_hash(cached_clip) == cached_hash.read_text():
                shutil.copyfile(cached_clip, clip)
            else:
                (render_card if renderer == "cards" else render_manim)(scene, clip, scene_work)
                # Atomic replace; concurrent identical renders produce the same cache contract.
                with tempfile.NamedTemporaryFile(dir=cache, delete=False) as entry:
                    cache_tmp = Path(entry.name)
                try:
                    shutil.copyfile(clip, cache_tmp)
                    cache_tmp.replace(cached_clip)
                    cached_hash.write_text(file_hash(clip))
                finally:
                    cache_tmp.unlink(missing_ok=True)
            clips.append(clip)
        # Controlled relative filenames prevent concat path injection.
        for i, clip in enumerate(clips):
            shutil.copyfile(clip, work / f"clip-{i}.mp4")
        concat = work / "clips.txt"
        concat.write_text("".join(f"file 'clip-{i}.mp4'\n" for i in range(len(clips))))
        video = work / "preview.mp4"
        args = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "concat", "-safe", "1", "-i", str(concat)]
        if audio:
            args += ["-i", audio["path"], "-map", "0:v:0", "-map", "1:a:0", "-af", "apad", "-c:a", "aac", "-b:a", "128k"]
        else:
            args += ["-an"]
        args += ["-t", str(seconds), "-c:v", "copy", "-movflags", "+faststart", str(video)]
        run(args)
        info = probe(video)
        actual_duration = float(info["format"]["duration"])
        if abs(actual_duration - seconds) > 0.25:
            raise MechaError("Rendered duration differs from the storyboard")
        if store.current(episode)["revision"] != revision:
            raise MechaError("Episode changed during rendering; retry the current revision")
        latest_audio = store.get_audio(episode)
        if (latest_audio["hash"] if latest_audio else None) != (audio["hash"] if audio else None):
            raise MechaError("Narration changed during rendering; retry")
        (work / "captions.srt").write_text(subtitles(doc), encoding="utf-8")
        (work / "script.md").write_text("\n\n".join(f"## {s['title']}\n\n{s['narration']}" for s in doc["scenes"]), encoding="utf-8")
        files = {name: file_hash(work / name) for name in ("preview.mp4", "captions.srt", "script.md")}
        manifest = {"episode": episode, "revision": revision, "document_hash": current["hash"], "key": key,
                    "renderer": renderer, "template_version": TEMPLATE_VERSION, "final_proof": final,
                    "silent": audio is None, "audio_hash": audio["hash"] if audio else None,
                    "duration_seconds": actual_duration, "caption_alignment": "scene-level, not word-aligned",
                    "created_at": now(), "files": files,
                    "limitations": ["No publishing or paid model calls", "No automatic audio alignment or loudness mastering",
                                    "Card renderer is a storyboard, orbit template is illustrative and not to scale"]}
        (work / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        dest.mkdir(exist_ok=True)
        for name in (*files, "manifest.json"):
            (work / name).replace(dest / name)
    with store.db() as db:
        db.execute("INSERT INTO renders VALUES(?,?,?,?,?)", (episode, revision, key, canonical(manifest), now()))
    return manifest | {"cached": False, "directory": str(dest)}
