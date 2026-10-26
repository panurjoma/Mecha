"""Draw the price end card for one product from input/<id>/price.json.

usage: python make_endcard.py <video-id> --format short|video --lang en
short = 1080x1920 portrait, video = 1920x1080 landscape (sizes come from video.json).
Output: input/<id>/endcard_<format>_<lang>.png. A hand-made input/<id>/endcard_<format>.png wins in edit_short.py.
"""
import argparse

from PIL import Image, ImageDraw, ImageFont

from common import ROOT, find_font, fmt, load_json, video_dir


def money(v, cur):
    return f"{cur}{v:.2f}"


def draw(video_id, kind, lang):
    chan = load_json(ROOT / "config" / "channel.json")
    vdir = video_dir(video_id)
    meta = load_json(vdir / "video.json")
    f_ = fmt(meta, kind)
    W, H = f_["w"], f_["h"]
    price = load_json(vdir / "price.json")
    lab = chan["endcard_labels"][lang]
    c = chan["colors"]
    cur = chan["currency"]
    total = round(sum(i["price"] for i in price["items"]), 2)
    per = round(total / price["servings"], 2)
    title = meta["title"][lang]

    img = Image.new("RGB", (W, H), c["cream"])
    d = ImageDraw.Draw(img)
    font = lambda size, bold=True: ImageFont.truetype(find_font(bold), size)
    icon = ROOT / "brand" / "icon.png"

    def round_icon(size):
        ic = Image.open(icon).convert("RGB").resize((size, size))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
        return ic, mask

    def wrap(text, fnt, max_w):
        lines, cur_line = [], ""
        for w in text.split():
            t = (cur_line + " " + w).strip()
            if d.textlength(t, font=fnt) > max_w and cur_line:
                lines.append(cur_line)
                cur_line = w
            else:
                cur_line = t
        return lines + [cur_line]

    def item_rows(x0, x1, y, step, size, price_size):
        for it in price["items"]:
            name, fs = it[lang], size
            while d.textlength(name, font=font(fs, False)) > (x1 - x0) - 220 and fs > 24:
                fs -= 2
            d.text((x0, y), name, font=font(fs, False), fill=c["charcoal"], anchor="lm")
            d.text((x1, y), money(it["price"], cur), font=font(price_size), fill=c["charcoal"], anchor="rm")
            y += step
            d.line([x0, y - step / 2, x1, y - step / 2], fill=c["sand"], width=3)
        return y

    if H >= W:  # portrait (short)
        d.rectangle([0, 0, W, 330], fill=c["tomato"])
        if icon.exists():
            ic, mask = round_icon(200)
            img.paste(ic, (440, 60), mask)
        d.text((W / 2, 285), chan["name"], font=font(52), fill=c["cream"], anchor="mm")
        y = 440
        for ln in wrap(title, font(60), W - 140):
            d.text((W / 2, y), ln, font=font(60), fill=c["charcoal"], anchor="mm")
            y += 76
        y = item_rows(90, W - 90, y + 90, 78, 40, 44)
        top = max(y + 30, 1240)
        d.rounded_rectangle([70, top, W - 70, top + 360], radius=44, fill=c["tomato"])
        d.text((W / 2, top + 80), f"{lab['total']} {money(total, cur)}  ·  {lab['serves'].format(n=price['servings'])}",
               font=font(50), fill=c["cream"], anchor="mm")
        d.text((W / 2, top + 220), money(per, cur), font=font(190), fill="white", anchor="mm")
        d.text((W / 2, top + 320), lab["per"], font=font(52), fill=c["cream"], anchor="mm")
        d.text((W / 2, H - 80), lab["note"], font=font(34, False), fill=c["charcoal"], anchor="mm")
    else:  # landscape (video): ingredient list on the left, big price on the right
        split = int(W * 0.60)
        d.rectangle([split, 0, W, H], fill=c["tomato"])
        y = 120
        for ln in wrap(title, font(64), split - 180):
            d.text((90, y), ln, font=font(64), fill=c["charcoal"], anchor="lm")
            y += 80
        item_rows(90, split - 90, y + 70, 86, 38, 42)
        d.text((90, H - 60), lab["note"], font=font(30, False), fill=c["charcoal"], anchor="lm")
        cx = split + (W - split) / 2
        if icon.exists():
            ic, mask = round_icon(170)
            img.paste(ic, (int(cx - 85), 90), mask)
        d.text((cx, 310), chan["name"], font=font(48), fill=c["cream"], anchor="mm")
        d.text((cx, 470), f"{lab['total']} {money(total, cur)}", font=font(54), fill=c["cream"], anchor="mm")
        d.text((cx, 640), money(per, cur), font=font(190), fill="white", anchor="mm")
        d.text((cx, 770), lab["per"], font=font(56), fill=c["cream"], anchor="mm")
        d.text((cx, 850), lab["serves"].format(n=price["servings"]), font=font(40), fill=c["cream"], anchor="mm")

    out = vdir / f"endcard_{kind}_{lang}.png"
    img.save(out)
    print(out, "total", total, "per serving", per)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    draw(a.video_id, a.format, a.lang)
