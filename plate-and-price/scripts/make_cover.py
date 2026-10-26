"""Make the cover card shown at the start of the short (1080x1920) and a 1920x1080 YouTube thumbnail.

usage: python make_cover.py video-001 --lang en
Uses one real frame of the dish from raw.mp4 (video.json "cover.frame_time"), the title and the price per serving.
Output: input/<id>/cover_<lang>.png and thumbnail_<lang>.png. A hand-made cover.png in the folder wins in edit_short.py.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from common import ROOT, find_ffmpeg, find_font, load_json


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


def gradient(size, top_alpha, bottom_alpha):
    w, h = size
    g = Image.new("L", (1, h))
    for y in range(h):
        t = y / (h - 1)
        g.putpixel((0, y), int(top_alpha * (1 - t) ** 2 + bottom_alpha * t ** 2))
    return g.resize((w, h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    chan = load_json(ROOT / "config" / "channel.json")
    c = chan["colors"]
    vdir = ROOT / "input" / a.video_id
    meta = load_json(vdir / "video.json")
    price = load_json(vdir / "price.json")
    per = round(sum(i["price"] for i in price["items"]) / price["servings"], 2)
    title = meta["title"][a.lang]
    per_label = chan["endcard_labels"][a.lang]["per"]

    with tempfile.TemporaryDirectory() as tmp:
        frame = Path(tmp) / "f.png"
        subprocess.run([find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y", "-ss", str(meta["cover"]["frame_time"]),
                        "-i", str(vdir / meta["raw"]), "-frames:v", "1", str(frame)], check=True)
        photo = ImageEnhance.Contrast(ImageEnhance.Brightness(Image.open(frame).convert("RGB")).enhance(1.3)).enhance(1.1)
    f = lambda s, b=True: ImageFont.truetype(find_font(b), s)

    # ---- 9:16 cover
    W, H = 1080, 1920
    im = photo.resize((W, H), Image.LANCZOS).convert("RGBA")
    shade = Image.new("RGBA", (W, H), (20, 14, 10, 0))
    shade.putalpha(gradient((W, H), 170, 215))
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    pill_w = 520
    d.rounded_rectangle([(W - pill_w) / 2, 150, (W + pill_w) / 2, 250], radius=50, fill=c["tomato"])
    d.text((W / 2, 200), chan["name"].upper(), font=f(46), fill="white", anchor="mm")
    lines = wrap(d, title, f(104), W - 150)
    y = 1060
    for ln in lines:
        d.text((W / 2, y), ln, font=f(104), fill="white", anchor="mm", stroke_width=3, stroke_fill=(20, 14, 10))
        y += 128
    cx, cy, r = W / 2, 1650, 140
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c["tomato"], outline=c["cream"], width=8)
    d.text((cx, cy - 18), f"{chan['currency']}{per:.0f}", font=f(130), fill="white", anchor="mm")
    d.text((cx, cy + 82), per_label, font=f(38), fill=c["cream"], anchor="mm")
    im.convert("RGB").save(vdir / f"cover_{a.lang}.png")

    # ---- 16:9 thumbnail: blurred backdrop, text left, vertical photo right
    TW, TH = 1920, 1080
    bg = photo.resize((TW, int(TW * photo.height / photo.width)), Image.LANCZOS)
    bg = bg.crop((0, (bg.height - TH) // 2, TW, (bg.height - TH) // 2 + TH)).filter(ImageFilter.GaussianBlur(28))
    bg = Image.alpha_composite(bg.convert("RGBA"), Image.new("RGBA", (TW, TH), (20, 14, 10, 150)))
    shot = photo.resize((int(TH * 0.92 * photo.width / photo.height), int(TH * 0.92)), Image.LANCZOS)
    bg.paste(shot, (TW - shot.width - 90, (TH - shot.height) // 2))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle([90, 90, 90 + 520, 190], radius=50, fill=c["tomato"])
    d.text((350, 140), chan["name"].upper(), font=f(46), fill="white", anchor="mm")
    y = 330
    for ln in wrap(d, title, f(116), 980):
        d.text((90, y), ln, font=f(116), fill="white", anchor="lm", stroke_width=3, stroke_fill=(20, 14, 10))
        y += 140
    d.rounded_rectangle([90, y + 40, 90 + 560, y + 230], radius=40, fill=c["tomato"])
    d.text((90 + 280, y + 112), f"{chan['currency']}{per:.2f}", font=f(100), fill="white", anchor="mm")
    d.text((90 + 280, y + 188), per_label, font=f(40), fill=c["cream"], anchor="mm")
    bg.convert("RGB").save(vdir / f"thumbnail_{a.lang}.png")
    print("wrote", vdir / f"cover_{a.lang}.png", vdir / f"thumbnail_{a.lang}.png")


if __name__ == "__main__":
    main()
