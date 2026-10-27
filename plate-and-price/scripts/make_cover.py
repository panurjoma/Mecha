"""Cover card for one product: an AI-generated image of the dish plus the channel branding.

usage: python make_cover.py <video-id> --format short|short_ia|video --lang en
Background: the AI image named in video.json cover.ai ("9x16" for the short, "16x9" for the video). If that file is
missing, run make_cover_ai.py first; as a last resort a frame of the real footage is used (a warning is printed).
Overlay: channel pill, recipe title, price per serving. Output: input/<id>/cover_<format>_<lang>.png.
For the video format the same image also becomes thumbnail_<lang>.png (YouTube thumbnail, 1920x1080).
A hand-made input/<id>/cover_<format>.png wins in edit_short.py.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from common import ROOT, find_ffmpeg, find_font, fmt, load_json, video_dir


def wrap(d, text, font, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + [cur]


def vgradient(size, top_alpha, bottom_alpha):
    w, h = size
    g = Image.new("L", (1, h))
    for y in range(h):
        t = y / (h - 1)
        g.putpixel((0, y), int(top_alpha * (1 - t) ** 2 + bottom_alpha * t ** 2))
    return g.resize((w, h))


def hgradient(size, left_alpha):
    w, h = size
    g = Image.new("L", (w, 1))
    for x in range(w):
        t = x / (w - 1)
        g.putpixel((x, 0), int(left_alpha * max(0.0, 1 - t / 0.75) ** 1.5))
    return g.resize((w, h))


def cover_fill(img, w, h):
    """Scale and centre-crop to exactly w x h."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def background(vdir, meta, ratio, w, h):
    ai = vdir / meta["cover"]["ai"][ratio]
    if ai.exists():
        return cover_fill(Image.open(ai).convert("RGB"), w, h)
    print(f"WARNING: {ai.name} not found, using a frame of the real footage. Run make_cover_ai.py for the AI cover.")
    with tempfile.TemporaryDirectory() as tmp:
        frame = Path(tmp) / "f.png"
        subprocess.run([find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss",
                        str(meta["cover"]["frame_time_fallback"]), "-i", str(vdir / meta["raw"]), "-frames:v", "1", str(frame)],
                       check=True)
        photo = ImageEnhance.Contrast(ImageEnhance.Brightness(Image.open(frame).convert("RGB")).enhance(1.3)).enhance(1.1)
    return cover_fill(photo, w, h)


def make(video_id, kind, lang):
    chan = load_json(ROOT / "config" / "channel.json")
    c = chan["colors"]
    vdir = video_dir(video_id)
    meta = load_json(vdir / "video.json")
    price = load_json(vdir / "price.json")
    f_ = fmt(meta, kind)
    W, H = f_["w"], f_["h"]
    per = round(sum(i["price"] for i in price["items"]) / price["servings"], 2)
    title = meta["title"][lang]
    per_label = chan["endcard_labels"][lang]["per"]
    font = lambda s, b=True: ImageFont.truetype(find_font(b), s)
    dark = (20, 14, 10)

    if H >= W:  # 9:16 short cover
        phone_safe = f_.get("phone_safe_cover", False)
        im = background(vdir, meta, "9x16", W, H).convert("RGBA")
        shade = Image.new("RGBA", (W, H), dark + (0,))
        shade.putalpha(vgradient((W, H), 80, 150))
        im = Image.alpha_composite(im, shade)
        d = ImageDraw.Draw(im)
        pill_w = 520
        d.rounded_rectangle([(W - pill_w) / 2, 150, (W + pill_w) / 2, 250], radius=50, fill=c["tomato"])
        d.text((W / 2, 200), chan["name"].upper(), font=font(46), fill="white", anchor="mm")
        d.text((W / 2, 295), chan["tagline"][lang], font=font(40), fill="white", anchor="mm", stroke_width=3, stroke_fill=dark)
        title_size = 96 if phone_safe else 104
        y = 870 if phone_safe else 1060
        for ln in wrap(d, title, font(title_size), W - 180):
            d.text((W / 2, y), ln, font=font(title_size), fill="white", anchor="mm", stroke_width=3, stroke_fill=dark)
            y += 112 if phone_safe else 128
        cx, cy, r = W / 2, (1360 if phone_safe else 1650), 165
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c["tomato"], outline=c["cream"], width=8)
        d.text((cx, cy - 22), (f"{chan['currency']}{per:.2f}" if lang == "en" else f"{per:.2f}".replace(".", ",") + f" {chan['currency']}"), font=font(80 if phone_safe else 100), fill="white", anchor="mm")
        d.text((cx, cy + (48 if phone_safe else 66)), per_label, font=font(36), fill=c["cream"], anchor="mm")
        if phone_safe:
            d.text((cx, cy + 100), "Estimate" if lang == "en" else "Estimado", font=font(32), fill=c["cream"], anchor="mm")
    else:  # 16:9 video cover and thumbnail
        im = background(vdir, meta, "16x9", W, H).convert("RGBA")
        shade = Image.new("RGBA", (W, H), dark + (0,))
        shade.putalpha(hgradient((W, H), 215))
        im = Image.alpha_composite(im, shade)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([90, 90, 90 + 520, 190], radius=50, fill=c["tomato"])
        d.text((350, 140), chan["name"].upper(), font=font(46), fill="white", anchor="mm")
        for size in (112, 100, 92, 84, 76):  # long titles shrink so they stay within three lines
            lines = wrap(d, title, font(size), 900)
            if len(lines) <= 3:
                break
        y = 320
        for ln in lines:
            d.text((90, y), ln, font=font(size), fill="white", anchor="lm", stroke_width=3, stroke_fill=dark)
            y += round(size * 1.2)
        top = H - 90 - 190  # price badge sits at a fixed place at the bottom, whatever the title length
        d.rounded_rectangle([90, top, 90 + 560, top + 190], radius=40, fill=c["tomato"])
        d.text((90 + 280, top + 72), (f"{chan['currency']}{per:.2f}" if lang == "en" else f"{per:.2f}".replace(".", ",") + f" {chan['currency']}"), font=font(100), fill="white", anchor="mm")
        d.text((90 + 280, top + 152), per_label, font=font(40), fill=c["cream"], anchor="mm")

    out = vdir / f"cover_{kind}_{lang}.png"
    im.convert("RGB").save(out)
    print("wrote", out)
    if kind == "video":
        im.convert("RGB").save(vdir / f"thumbnail_{lang}.png")
        print("wrote", vdir / f"thumbnail_{lang}.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "short_ia", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    make(a.video_id, a.format, a.lang)
