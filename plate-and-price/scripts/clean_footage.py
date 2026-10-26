"""Stage 3: studio-style clean-up of a rough cut (glare, noise, white balance, colour, a touch of sharpness).

usage: python clean_footage.py <video-id> --format short|video [--force]
Reads <OUTPUT_DIR>/<id>/layers/rough_<format>.mp4 and writes layers/clean_<format>.mp4 (also copied to
<OUTPUT_DIR>/<id>/clean_<format>.mp4), keeping the clips' sound. Settings: video.json "clean" (all optional):
  denoise   [luma_spatial, chroma_spatial, luma_temporal, chroma_temporal] for hqdn3d (default 3,2,6,6)
  highlights  top of the tone curve (0..1, default 0.94): lower values tame blown whites and glints more
  shadows     lift for dark areas (default 0.03)
  warmth      colour temperature in kelvin, 6500 = neutral (default 6500; lower = warmer)
  saturation, contrast, sharpen (default 1.08, 1.04, 0.35)
The sparkle of small bright reflections is first reduced in the cut (the "shutter" setting); this stage handles the rest.
Cached: only a change to these settings or to the rough cut rebuilds it.
"""
import argparse
import shutil

from common import OUTPUT_DIR, find_ffmpeg, load_json, run, video_dir
from layers import build_cached, code, digest, sig

DEFAULTS = {"denoise": [3, 2, 6, 6], "highlights": 0.94, "shadows": 0.03, "warmth": 6500,
            "saturation": 1.08, "contrast": 1.04, "sharpen": 0.35}


def clean_filters(c):
    d = c["denoise"]
    hi, lo = c["highlights"], c["shadows"]
    f = ["scale=in_range=pc:out_range=tv:flags=lanczos",  # GoPro files are full range: put them in normal video range
         f"hqdn3d={d[0]}:{d[1]}:{d[2]}:{d[3]}",
         f"curves=all='0/{lo} 0.3/0.3 0.7/0.69 0.9/{hi * 0.94:.3f} 1/{hi}'"]  # lift blacks a little, squeeze the whites
    if c["warmth"] != 6500:
        f.append(f"colortemperature=temperature={c['warmth']}")
    f += [f"eq=saturation={c['saturation']}:contrast={c['contrast']}", f"unsharp=5:5:{c['sharpen']}:5:5:0", "format=yuv420p"]
    return f


def build_clean(tmp, ffmpeg, rough, c, crf):
    run([ffmpeg, "-hide_banner", "-y", "-i", str(rough), "-vf", ",".join(clean_filters(c)), "-c:v", "libx264", "-preset", "slow",
         "-crf", str(crf), "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-c:a", "copy", "-movflags", "+faststart", str(tmp)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    meta = load_json(video_dir(a.video_id) / "video.json")
    c = {**DEFAULTS, **meta.get("clean", {}), **meta["formats"][a.format].get("clean", {})}
    out_dir = OUTPUT_DIR / a.video_id
    rough = out_dir / "layers" / f"rough_{a.format}.mp4"
    if not rough.exists():
        raise SystemExit("no rough cut yet: run cut_rough.py first")
    crf = 14
    layer = out_dir / "layers" / f"clean_{a.format}.mp4"
    build_cached(layer, digest("clean", code(build_clean), code(clean_filters), sig(rough), c, crf),
                 lambda t: build_clean(t, find_ffmpeg(), rough, c, crf), f"clean {a.format}", a.force)
    final = out_dir / f"clean_{a.format}.mp4"
    shutil.copyfile(layer, final)
    print(f"clean={final}")


if __name__ == "__main__":
    main()
