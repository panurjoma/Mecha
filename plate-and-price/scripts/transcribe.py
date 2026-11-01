"""Transcribe the owner's voice in every recording of a recipe (local Whisper, no cloud, no key).

    uv run --with faster-whisper --with imageio-ffmpeg python scripts/transcribe.py <recipe-id> [--lang es] [--model large-v3]

Reads input/<id>/*.MP4 (GoPro audio), writes input/<id>/transcript.json:
    {"lang": "es", "files": {"GH011620.MP4": {"duration": 21.0, "segments": [{"start": 0.0, "end": 2.4, "text": "..."}]}}}
and input/<id>/transcript.txt (readable, one block per file). Segment times are seconds inside that file, so they can be
used directly as `src_start` / `dur` when selecting moments (directive 18, stage 1) and as the source of the voice script.
Cached per file: a file already in transcript.json is skipped unless --force is given.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg

# faster-whisper (CTranslate2) needs cublas/cudnn DLLs; the PyTorch wheels ship them, so point Windows at them.
try:
    import os
    import torch  # noqa: F401
    _lib = Path(torch.__file__).parent / "lib"
    if _lib.exists():
        os.add_dll_directory(str(_lib))
        os.environ["PATH"] = str(_lib) + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent


def extract_audio(src: Path, dst: Path):
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
                    str(dst)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recipe")
    ap.add_argument("--lang", default="es")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    folder = ROOT / "input" / a.recipe
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".mp4")
    out_json = folder / "transcript.json"
    data = json.loads(out_json.read_text(encoding="utf-8")) if out_json.exists() else {"lang": a.lang, "files": {}}

    from faster_whisper import WhisperModel
    try:
        model = WhisperModel(a.model, device="cuda", compute_type="float16")
    except Exception as e:  # not enough VRAM or no CUDA libs
        print("float16 failed, trying int8_float16:", e, file=sys.stderr)
        try:
            model = WhisperModel(a.model, device="cuda", compute_type="int8_float16")
        except Exception as e2:
            print("GPU failed, using CPU int8:", e2, file=sys.stderr)
            model = WhisperModel(a.model, device="cpu", compute_type="int8")

    def run(m, wav):
        segs, info = m.transcribe(str(wav), language=a.lang, vad_filter=True, beam_size=5, condition_on_previous_text=False)
        return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs], info

    for f in files:
        if f.name in data["files"] and not a.force:
            continue
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "a.wav"
            extract_audio(f, wav)
            try:
                segments, info = run(model, wav)
            except RuntimeError as e:  # CUDA libraries missing at run time: fall back to the CPU
                print("GPU transcription failed, using CPU int8:", e, file=sys.stderr)
                model = WhisperModel(a.model, device="cpu", compute_type="int8")
                segments, info = run(model, wav)
        data["files"][f.name] = {"duration": round(info.duration, 2), "segments": segments}
        out_json.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f.name, f"{info.duration:.0f}s", len(segments), "segments", flush=True)

    lines = []
    for name, d in sorted(data["files"].items()):
        lines.append(f"=== {name} ({d['duration']:.0f}s)")
        for s in d["segments"]:
            lines.append(f"[{s['start']:6.1f}-{s['end']:6.1f}] {s['text']}")
        lines.append("")
    (folder / "transcript.txt").write_text("\n".join(lines), encoding="utf-8")
    print("wrote", out_json)


if __name__ == "__main__":
    main()
