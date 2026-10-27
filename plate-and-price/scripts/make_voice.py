"""Make a calm voice-over from the captions with a free text-to-speech engine (edge-tts), one line per caption.

usage: python make_voice.py <video-id> --format video --lang en [--force]
Output: input/<id>/voice_<format>_tts_<lang>.wav (same length as the video). It is a layer: if the captions, the voice
name, the rate and the timing are unchanged, the file is reused and nothing is generated. If you record your own voice,
save it as input/<id>/voice_<format>_<lang>.wav on the output timeline; edit_short.py prefers that file.

The voice is never rushed: speed is only raised up to video.json formats.<format>.tempo_max (default 1.08), and a
warning is printed for any caption whose speech is still longer than its window (shorten that caption or widen it).
edge-tts is free and needs no key, but it sends the caption text to Microsoft's online voice service (unofficial API).
"""
import argparse
import asyncio
import re
import subprocess
import tempfile
from pathlib import Path

from common import find_ffmpeg, fmt, load_json, parse_srt, run, video_dir
from layers import build_cached, code, digest, sig


def duration(ffmpeg, path):
    err = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def synth(cues, voice, rate, tmp):
    import edge_tts
    files = []
    for i, (_, _, text) in enumerate(cues):
        p = Path(tmp) / f"c{i}.mp3"
        for attempt in range(1, 5):  # the free service sometimes answers with no audio: retry with a growing pause
            try:
                await edge_tts.Communicate(" ".join(text.split()), voice, rate=rate).save(str(p))
                break
            except edge_tts.exceptions.NoAudioReceived:
                if attempt == 4:
                    raise
                await asyncio.sleep(2 * attempt)
        files.append(p)
    return files


def build_voice(out, ffmpeg, cues, cfg, tempo_max, total):
    with tempfile.TemporaryDirectory() as tmp:
        files = asyncio.run(synth(cues, cfg["voice"], cfg["rate"], tmp))
        cmd, chains = [ffmpeg, "-hide_banner", "-y"], []
        for i, ((start, end, text), f) in enumerate(zip(cues, files)):
            trimmed = f.with_suffix(".wav")  # the service pads each line with silence: cut it so the length is the speech itself
            trim = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05"
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(f), "-af", f"{trim},areverse,{trim},areverse",
                            str(trimmed)], check=True)
            f = trimmed
            natural = duration(ffmpeg, f)
            window = end - start
            tempo = min(max(natural / window, 1.0), tempo_max)
            if natural / tempo > window:
                print(f"WARNING caption {i + 1}: speech {natural / tempo:.1f}s is longer than its window {window:.1f}s")
            cmd += ["-i", str(f)]
            ms = round(start * 1000)
            chains.append(f"[{i}:a]atempo={tempo:.3f},adelay={ms}|{ms},aformat=sample_rates=44100:channel_layouts=stereo[a{i}]")
        chains.append("".join(f"[a{i}]" for i in range(len(files))) + f"amix=inputs={len(files)}:normalize=0,apad,atrim=0:{total}[out]")
        graph = Path(tmp) / "g.txt"
        graph.write_text(";\n".join(chains), encoding="utf-8")
        run(cmd + ["-filter_complex_script", str(graph), "-map", "[out]", "-ar", "44100", str(out)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="video", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, a.format)
    cfg = meta["voice"][a.lang]
    cap_file = vdir / f_["captions"][a.lang]
    voice_script = cap_file.with_name(cap_file.stem + ".voice.srt")  # made by make_captions.py: captions + cover and end card lines
    if voice_script.exists():
        cap_file = voice_script
    cues = parse_srt(cap_file)
    tempo_max = f_.get("tempo_max", 1.08)
    ffmpeg = find_ffmpeg()
    out = vdir / f"voice_{a.format}_tts_{a.lang}.wav"
    key = digest("voice", code(build_voice), code(synth), sig(cap_file), cfg, tempo_max, f_["total"])
    build_cached(out, key, lambda tmp: build_voice(tmp, ffmpeg, cues, cfg, tempo_max, f_["total"]),
                 f"voice {a.format} {a.lang} ({cfg['voice']})", a.force)
    print("voice file:", out)


if __name__ == "__main__":
    main()
