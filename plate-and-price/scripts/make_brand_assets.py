"""Draw the channel brand assets locally (exact spelling, reproducible): icon, watermark, banner.

usage: python make_brand_assets.py        -> brand/icon.png (1024), brand/watermark.png (512, white on transparent),
                                              brand/banner.png (2560x1440)
"""
from PIL import Image, ImageDraw, ImageFont

from common import ROOT, find_font, load_json

OUT = ROOT / "brand"
SS = 2  # supersampling for smooth edges


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(size, bold=True):
    return ImageFont.truetype(find_font(bold), size)


def plate_mark(size, plate, rim, tag, tag_text, bg=None):
    """Plate seen from above + a price tag tied to its rim. Returns RGBA."""
    s = size * SS
    im = Image.new("RGBA", (s, s), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = s / 2
    r = s * 0.30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=plate)
    r2 = r * 0.72
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=rim, width=int(s * 0.018))
    # fork and knife flanking the plate
    for sx in (-1, 1):
        x = cx + sx * s * 0.43
        d.rounded_rectangle([x - s * 0.012, cy - s * 0.17, x + s * 0.012, cy + s * 0.2], radius=int(s * 0.012), fill=plate)
    for k in (-1, 0, 1):
        x = cx - s * 0.43 + k * s * 0.022
        d.rounded_rectangle([x - s * 0.006, cy - s * 0.22, x + s * 0.006, cy - s * 0.1], radius=int(s * 0.006), fill=plate)
    d.ellipse([cx + s * 0.43 - s * 0.03, cy - s * 0.24, cx + s * 0.43 + s * 0.03, cy - s * 0.08], fill=plate)
    # price tag on its own layer so it can be rotated
    tw, th = int(s * 0.26), int(s * 0.16)
    tl = Image.new("RGBA", (tw + int(s * 0.1), th + int(s * 0.1)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    ox, oy = int(s * 0.05), int(s * 0.05)
    cut = int(th * 0.4)
    td.polygon([(ox + cut, oy), (ox + tw, oy), (ox + tw, oy + th), (ox + cut, oy + th), (ox, oy + th / 2)], fill=tag)
    hole = int(th * 0.09)
    td.ellipse([ox + cut * 0.9 - hole, oy + th / 2 - hole, ox + cut * 0.9 + hole, oy + th / 2 + hole], fill=bg or (0, 0, 0, 0))
    tf = ImageFont.truetype(find_font(True), int(th * 0.62))
    td.text((ox + tw * 0.62, oy + th / 2), tag_text, font=tf, fill=plate if plate != tag else rim, anchor="mm")
    tl = tl.rotate(28, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(tl, (int(cx + s * 0.04), int(cy - r * 1.12)))
    return im.resize((size, size), Image.LANCZOS)


def main():
    c = load_json(ROOT / "config" / "channel.json")
    col = {k: rgb(v) for k, v in c["colors"].items()}
    OUT.mkdir(exist_ok=True)

    # icon: tomato square, cream plate, charcoal tag
    icon = plate_mark(1024, col["cream"], col["sand"], col["charcoal"], "€", bg=col["tomato"] + (255,))
    icon.convert("RGB").save(OUT / "icon.png")

    # watermark: white mark on transparent, semi transparent by default
    wm = plate_mark(512, (255, 255, 255, 235), (255, 255, 255, 235), (255, 255, 255, 235), "€")
    # punch the euro sign out of the tag so it stays readable on a white mark
    wm.save(OUT / "watermark.png")

    # banner 2560x1440; YouTube safe area is the centre 1546x423
    W, H = 2560, 1440
    b = Image.new("RGB", (W, H), col["cream"])
    d = ImageDraw.Draw(b)
    for (x, y, r, fill) in [(120, 180, 330, col["sand"]), (2440, 1260, 380, col["sand"]), (2300, 120, 150, col["tomato"]),
                            (260, 1300, 120, col["tomato"])]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    mark = plate_mark(360, col["cream"], col["sand"], col["charcoal"], "€", bg=col["tomato"] + (255,))
    mark_mask = Image.new("L", (360, 360), 0)
    ImageDraw.Draw(mark_mask).rounded_rectangle([0, 0, 359, 359], radius=80, fill=255)
    b.paste(mark.convert("RGB"), (W // 2 - 720, H // 2 - 215), mark_mask)
    name_f, tag_f = font(160), font(54, False)
    x0 = W // 2 - 310
    d.text((x0, H // 2 - 80), "Plate ", font=name_f, fill=col["charcoal"], anchor="lm")
    x1 = x0 + d.textlength("Plate ", font=name_f)
    d.text((x1, H // 2 - 80), "&", font=name_f, fill=col["tomato"], anchor="lm")
    x2 = x1 + d.textlength("& ", font=name_f)
    d.text((x2, H // 2 - 80), "Price", font=name_f, fill=col["charcoal"], anchor="lm")
    d.text((x0, H // 2 + 60), c["tagline"]["en"], font=tag_f, fill=col["tomato"], anchor="lm")
    d.text((x0, H // 2 + 130), c["tagline"]["es"], font=font(40, False), fill=col["charcoal"], anchor="lm")
    b.save(OUT / "banner.png")
    print("wrote", [p.name for p in OUT.iterdir() if p.suffix == ".png"])


if __name__ == "__main__":
    main()
