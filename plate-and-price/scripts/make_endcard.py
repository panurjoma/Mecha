"""Draw the 1080x1920 price end card from input/<id>/price.json.

usage: python make_endcard.py video-001 --lang en
Output: input/<id>/endcard_<lang>.png. A hand-made input/<id>/endcard.png is used by edit_short.py if present.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

from common import ROOT, find_font, load_json

W, H = 1080, 1920


def money(v, cur):
    return f"{cur}{v:.2f}"


def draw(video_id, lang):
    chan = load_json(ROOT / "config" / "channel.json")
    vdir = ROOT / "input" / video_id
    meta = load_json(vdir / "video.json")
    price = load_json(vdir / "price.json")
    lab = chan["endcard_labels"][lang]
    c = chan["colors"]
    cur = chan["currency"]
    total = round(sum(i["price"] for i in price["items"]), 2)
    per = round(total / price["servings"], 2)

    img = Image.new("RGB", (W, H), c["cream"])
    d = ImageDraw.Draw(img)
    f = lambda size, bold=True: ImageFont.truetype(find_font(bold), size)

    d.rectangle([0, 0, W, 330], fill=c["tomato"])
    icon = ROOT / "brand" / "icon.png"
    if icon.exists():
        ic = Image.open(icon).convert("RGB").resize((200, 200))
        mask = Image.new("L", (200, 200), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, 199, 199], fill=255)
        img.paste(ic, (440, 60), mask)
    d.text((W / 2, 285), chan["name"], font=f(52), fill=c["cream"], anchor="mm")

    title = meta["title"][lang]
    words, lines, cur_line = title.split(), [], ""
    for w in words:
        t = (cur_line + " " + w).strip()
        if d.textlength(t, font=f(60)) > W - 140:
            lines.append(cur_line)
            cur_line = w
        else:
            cur_line = t
    lines.append(cur_line)
    y = 440
    for ln in lines:
        d.text((W / 2, y), ln, font=f(60), fill=c["charcoal"], anchor="mm")
        y += 76

    y += 50
    for it in price["items"]:
        name = it[lang]
        fs = 40
        while d.textlength(name, font=f(fs, False)) > 700 and fs > 28:
            fs -= 2
        d.text((90, y), name, font=f(fs, False), fill=c["charcoal"], anchor="lm")
        d.text((W - 90, y), money(it["price"], cur), font=f(44), fill=c["charcoal"], anchor="rm")
        y += 78
        d.line([90, y - 36, W - 90, y - 36], fill=c["sand"], width=3)

    box_top = max(y + 30, 1240)
    d.rounded_rectangle([70, box_top, W - 70, box_top + 360], radius=44, fill=c["tomato"])
    d.text((W / 2, box_top + 80), f"{lab['total']} {money(total, cur)}  ·  {lab['serves'].format(n=price['servings'])}",
           font=f(50), fill=c["cream"], anchor="mm")
    d.text((W / 2, box_top + 220), money(per, cur), font=f(190), fill="white", anchor="mm")
    d.text((W / 2, box_top + 320), lab["per"], font=f(52), fill=c["cream"], anchor="mm")
    d.text((W / 2, H - 80), lab["note"], font=f(34, False), fill=c["charcoal"], anchor="mm")

    out = vdir / f"endcard_{lang}.png"
    img.save(out)
    print(out, "total", total, "per serving", per)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    draw(a.video_id, a.lang)
