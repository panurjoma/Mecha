"""Write the caption files from the clip list, so captions always follow the cuts.

usage: python make_captions.py <video-id> --format short|short_ia|video --lang en
Each segment in video.json formats.<format>.segments may carry "caption": {"en": "...", "es": "..."}. This script puts each
caption on its clip and writes the .srt named in formats.<format>.captions.<lang>. When you add, remove, reorder or retime
a clip, run it again (run_pipeline.py does it for you) and every caption moves with its clip.
Timeline: [moving hook] -> cover card -> clips in order -> end card. A hook clip (the first segment, "hook": true) may have a
caption too. Short: the caption fills the clip minus 0.2 s; video: it starts 0.3 s in and ends 0.5 s before the cut, which is
the window the voice-over uses (see make_voice.py). Segments without a caption get none.
For a video with voice-over it also writes <captions>.voice.srt: the same lines plus formats.<format>.cover_caption and
end_caption (spoken over the cover card and the end card, not burned in). make_voice.py reads that file when it exists. Does nothing when no segment has one.
"""
import argparse

from common import fmt, load_json, video_dir, write_srt


def wrap(text, width):
    """Split a long caption into two balanced lines."""
    if len(text) <= width or " " not in text:
        return text
    words, best = text.split(), None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if best is None or abs(len(a) - len(b)) < abs(len(best[0]) - len(best[1])):
            best = (a, b)
    return best[0] + "\n" + best[1]


def voice_srt(f_, lang):
    """Path of the voice script: the captions plus voice-only lines (over the cover card and the end card)."""
    from pathlib import Path
    cap = Path(f_["captions"][lang])
    return cap.with_name(cap.stem + ".voice.srt")


def build_cues(f_, lang, voice=False):
    short = f_["h"] > f_["w"]
    width = 22 if short else 44
    cues, t, hook = [], 0.0, f_["hook_dur"]
    for i, s in enumerate(f_["segments"]):
        if i == 1 and hook:
            t = hook + f_["cover_dur"]  # the cover card sits between the hook and the first clip
        elif i == 0:
            t = 0.0 if hook else f_["cover_dur"]
        text = (s.get("caption") or {}).get(lang)
        if text:
            a, b = (t, t + s["dur"] - 0.2) if short else (t + 0.3, t + s["dur"] - 0.5)
            cues.append((a, b, wrap(text, width)))
        t += s["dur"]
    if voice:  # lines spoken over the cover card and the end card, never burned onto those cards
        cc = (f_.get("cover_caption") or {}).get(lang)
        if cc:
            c0 = hook + 0.0
            cues.append((c0 + 0.3, c0 + f_["cover_dur"] - 0.3, cc))
        ec = (f_.get("end_caption") or {}).get(lang)
        if ec:
            cues.append((t + 0.5, t + f_["endcard_dur"] - 0.5, ec))
        cues.sort()
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "short_ia", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    f_ = fmt(load_json(vdir / "video.json"), a.format)
    if not any((s.get("caption") or {}).get(a.lang) for s in f_["segments"]):
        print("no captions in the segments: the caption file is used as it is")
        return
    cues = build_cues(f_, a.lang)
    write_srt(vdir / f_["captions"][a.lang], cues)
    print(f"{len(cues)} captions written to {f_['captions'][a.lang]}")
    if f_["voice"]:
        vs = voice_srt(f_, a.lang)
        write_srt(vdir / vs, build_cues(f_, a.lang, voice=True))
        print(f"voice script written to {vs}")


if __name__ == "__main__":
    main()
