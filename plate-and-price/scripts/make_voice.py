"""Make a voice-over from the captions with a free text-to-speech engine (edge-tts), timed to each caption.

usage: python make_voice.py video-001 --lang en
Output: input/<id>/voice_tts_<lang>.wav (same length as the video). If you record your own voice, save it as
input/<id>/voice_<lang>.wav on the output timeline; edit_short.py --voice prefers that file over the generated one.

edge-tts is free and needs no key, but it sends the caption text to Microsoft's online voice service (unofficial API).
"""
import argparse
import asyncio
import re
import subprocess
import tempfile
from pathlib import Path

from common import ROOT, find_ffmpeg, load_json, parse_srt, run


def duration(ffmpeg, path):
    err = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def synth(cues, voice, rate, tmp):
    import edge_tts
    files = []
    for i, (_, _, text) in enumerate(cues):
        p = Path(tmp) / f"c{i}.mp3"
        await edge_tts.Communicate(" ".join(text.split()), voice, rate=rate).save(str(p))
        files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    vdir = ROOT / "input" / a.video_id
    meta = load_json(vdir / "video.json")
    cfg = meta["voice"][a.lang]
    cues = parse_srt(vdir / meta["captions"][a.lang])
    total = sum(s["dur"] for s in meta["segments"]) + meta["cover"]["dur"] + meta["endcard"]["dur"]
    ffmpeg = find_ffmpeg()

    with tempfile.TemporaryDirectory() as tmp:
        files = asyncio.run(synth(cues, cfg["voice"], cfg["rate"], tmp))
        cmd, chains = [ffmpeg, "-hide_banner", "-y"], []
        for i, ((start, end, _), f) in enumerate(zip(cues, files)):
            window = max(end - start - 0.1, 0.5)
            tempo = min(max(duration(ffmpeg, f) / window, 1.0), 1.4)  # speed up a little rather than overrun the caption
            cmd += ["-i", str(f)]
            ms = round(start * 1000)
            chains.append(f"[{i}:a]atempo={tempo:.3f},adelay={ms}|{ms},aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
        chains.append("".join(f"[a{i}]" for i in range(len(files))) + f"amix=inputs={len(files)}:normalize=0,apad,atrim=0:{total}[out]")
        graph = Path(tmp) / "g.txt"
        graph.write_text(";\n".join(chains), encoding="utf-8")
        out = vdir / f"voice_tts_{a.lang}.wav"
        run(cmd + ["-filter_complex_script", str(graph), "-map", "[out]", "-ar", "44100", str(out)])
    print("wrote", out)


if __name__ == "__main__":
    main()
