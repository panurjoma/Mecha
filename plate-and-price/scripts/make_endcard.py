"""Draw the price end card for one product from input/<id>/price.json.

usage: python make_endcard.py <video-id> --format short|short_ia|video --lang en
short = 1080x1920 portrait, video = 1920x1080 landscape (sizes come from video.json).
Output: input/<id>/endcard_<format>_<lang>.png. A hand-made input/<id>/endcard_<format>.png wins in edit_short.py.
"""
import argparse

from PIL import Image, ImageDraw, ImageFont

from common import ROOT, find_font, fmt, load_json, video_dir


LANG = "en"


def money(v, cur):
    """English: symbol first (EUR 1.90 as the symbol then the number); Spanish: 1,90 then the symbol."""
    return f"{cur}{v:.2f}" if LANG == "en" else f"{v:.2f}".replace(".", ",") + f" {cur}"


def draw(video_id, kind, lang):
    global LANG
    LANG = lang
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

    if H >= W and f_.get("phone_safe_card"):
        # Keep the full bill and its estimate label above the Shorts bottom controls.
        cx = W * 0.46
        d.rounded_rectangle([90, 150, W - 170, 245], radius=35, fill=c["tomato"])
        d.text((cx, 198), chan["name"], font=font(48), fill=c["cream"], anchor="mm")
        y = 330
        for ln in wrap(title, font(54), W - 240):
            d.text((cx, y), ln, font=font(54), fill=c["charcoal"], anchor="mm")
            y += 66
        top = max(490, y + 15)
        d.rounded_rectangle([90, top, W - 170, top + 330], radius=40, fill=c["tomato"])
        total_label = "Estimated total" if lang == "en" else "Total estimado"
        d.text((cx, top + 55), f"{total_label} {money(total, cur)}  ·  {lab['serves'].format(n=price['servings'])}",
               font=font(38), fill=c["cream"], anchor="mm")
        d.text((cx, top + 175), money(per, cur), font=font(168), fill="white", anchor="mm")
        d.text((cx, top + 280), lab["per"], font=font(48), fill=c["cream"], anchor="mm")
        item_rows(90, W - 170, top + 390, 66, 38, 40)
        d.text((cx, 1400), "Estimated cost · amounts used" if lang == "en" else "Coste estimado · cantidad usada",
               font=font(36, False), fill=c["charcoal"], anchor="mm")
        d.text((cx, 1470), lab["cta"], font=font(40), fill=c["tomato"], anchor="mm")
    elif H >= W:  # portrait (short)
        d.rectangle([0, 0, W, 330], fill=c["tomato"])
        if icon.exists():
            ic, mask = round_icon(200)
            img.paste(ic, (440, 60), mask)
        d.text((W / 2, 285), chan["name"], font=font(52), fill=c["cream"], anchor="mm")
        y = 405
        for ln in wrap(title, font(58), W - 140):
            d.text((W / 2, y), ln, font=font(58), fill=c["charcoal"], anchor="mm")
            y += 72
        top = y + 10  # price block first and big, above the bottom 20 % where the app draws its buttons
        d.rounded_rectangle([70, top, W - 70, top + 380], radius=44, fill=c["tomato"])
        d.text((W / 2, top + 70), f"{lab['total']} {money(total, cur)}  ·  {lab['serves'].format(n=price['servings'])}",
               font=font(50), fill=c["cream"], anchor="mm")
        d.text((W / 2, top + 215), money(per, cur), font=font(210), fill="white", anchor="mm")
        d.text((W / 2, top + 330), lab["per"], font=font(56), fill=c["cream"], anchor="mm")
        item_rows(90, W - 90, top + 380 + 70, 80, 42, 44)
        if lab.get("cta"):
            d.text((W / 2, H - 150), lab["cta"], font=font(48), fill=c["tomato"], anchor="mm")
        d.text((W / 2, H - 70), lab["note"], font=font(42, False), fill=c["charcoal"], anchor="mm")
    else:  # landscape (video): ingredient list on the left, big price on the right
        split = int(W * 0.60)
        d.rectangle([split, 0, W, H], fill=c["tomato"])
        y = 120
        for ln in wrap(title, font(64), split - 180):
            d.text((90, y), ln, font=font(64), fill=c["charcoal"], anchor="lm")
            y += 80
        item_rows(90, split - 90, y + 70, 86, 38, 42)
        d.text((90, H - 60), lab["note"], font=font(40, False), fill=c["charcoal"], anchor="lm")
        cx = split + (W - split) / 2
        if icon.exists():
            ic, mask = round_icon(170)
            img.paste(ic, (int(cx - 85), 90), mask)
        d.text((cx, 310), chan["name"], font=font(48), fill=c["cream"], anchor="mm")
        d.text((cx, 470), f"{lab['total']} {money(total, cur)}", font=font(54), fill=c["cream"], anchor="mm")
        d.text((cx, 640), money(per, cur), font=font(190), fill="white", anchor="mm")
        d.text((cx, 770), lab["per"], font=font(56), fill=c["cream"], anchor="mm")
        d.text((cx, 850), lab["serves"].format(n=price["servings"]), font=font(40), fill=c["cream"], anchor="mm")
        if lab.get("cta"):
            d.text((cx, 940), lab["cta"], font=font(44), fill="white", anchor="mm")

    out = vdir / f"endcard_{kind}_{lang}.png"
    img.save(out)
    print(out, "total", total, "per serving", per)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="short", choices=["short", "short_ia", "video"])
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    draw(a.video_id, a.format, a.lang)
