"""Write the YouTube title, description and tags for one product (short or video).

usage: python make_description.py <video-id> --format short|video --lang en [--llm]
Output: <OUTPUT_DIR>/<id>/description_<format>_<lang>.md with TITLE, DESCRIPTION and TAGS sections (paste them into
YouTube Studio) and a NOTES section for the owner (not for YouTube). English by default.

The text comes from templates plus the hook, closing line, keywords and hashtags in video.json "description", the price
list in price.json, and, for the video, the chapters in video.json formats.video.chapters (timestamps start at 0:00,
each chapter is at least 10 s, as YouTube requires). Tone: close and natural, like a friend in the kitchen.
--llm rewrites the hook with Claude or OpenAI (keys in .env) in the same tone; without it no key is needed.
"""
import argparse
import json

from common import OUTPUT_DIR, fmt, load_json, load_env, video_dir

T = {
    "en": {
        "short_title": "{title} for {per} a serving #Shorts",
        "video_title": "{title} | Dinner for two for {per} a serving",
        "costs": "What it costs (estimated supermarket prices)",
        "total": "Total {total} for {n}, which is {per} a serving.",
        "chapters": "Chapters",
        "music": "Music: {song} by {artist}",
        "short_price": "The whole dinner for {n} costs about {total}, so {per} a serving.",
    },
    "es": {
        "short_title": "{title} por {per} la ración #Shorts",
        "video_title": "{title} | Cena para dos por {per} la ración",
        "costs": "Lo que cuesta (precios estimados de supermercado)",
        "total": "Total {total} para {n}, es decir {per} por ración.",
        "chapters": "Capítulos",
        "music": "Música: {song} de {artist}",
        "short_price": "La cena entera para {n} cuesta unos {total}, o sea {per} por ración.",
    },
}


def money(v, lang):
    return f"€{v:.2f}" if lang == "en" else f"{v:.2f}".replace(".", ",") + " €"


def mmss(sec):
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"


def polish_hook(hook, lang):
    from llm_client import complete
    return complete(
        f"Rewrite this YouTube hook in {'English' if lang == 'en' else 'Spanish from Spain'} in a close, natural tone, like a "
        "friend talking in the kitchen: second person, short sentences, no marketing phrases, no emojis. Keep every fact "
        f"and the price. Return only the text.\n\n{hook}",
        system="You write friendly cooking-channel descriptions.").strip()


def build(video_id, kind, lang, use_llm=False):
    load_env()
    vdir = video_dir(video_id)
    meta = load_json(vdir / "video.json")
    price = load_json(vdir / "price.json")
    chan = load_json(vdir.parent.parent / "config" / "channel.json")
    f_ = fmt(meta, kind)
    t, d = T[lang], meta["description"]
    items = price["items"]
    total = round(sum(i["price"] for i in items), 2)
    per = round(total / price["servings"], 2)
    n = price["servings"]
    title = meta["title"][lang]
    hook = d["hook"][lang].format(per=money(per, lang))
    if use_llm:
        hook = polish_hook(hook, lang)

    if kind == "short":
        yt_title = t["short_title"].format(title=title, per=money(per, lang))
        body = [hook, "", t["short_price"].format(n=n, total=money(total, lang), per=money(per, lang)), "",
                d["closing"][lang], "", " ".join(d["hashtags"][lang] + ["#Shorts"])]
    else:
        yt_title = t["video_title"].format(title=title, per=money(per, lang))
        body = [hook, "", t["costs"]]
        body += [f"- {i[lang]}: {money(i['price'], lang)}" for i in items]
        body += [t["total"].format(total=money(total, lang), n=n, per=money(per, lang)), ""]
        chapters = f_.get("chapters", [])
        if chapters:
            starts = [c["at"] for c in chapters] + [f_["total"]]
            bad = [c for c, a, b in zip(chapters, starts, starts[1:]) if b - a < 10]
            if chapters[0]["at"] != 0 or len(chapters) < 3 or bad:
                raise SystemExit("chapters must start at 0:00, be at least 3, and last at least 10 s each")
            body += [t["chapters"]] + [f"{mmss(c['at'])} {c[lang]}" for c in chapters] + [""]
        song = meta["audio"].get("song", {})
        if song.get("licensed"):
            body += [t["music"].format(song=song["title"], artist=song["artist"]), ""]
        body += [d["closing"][lang], "", " ".join(d["hashtags"][lang])]

    notes = [f"Prices are estimates (price.json). Channel: {chan['name']}."]
    song = meta["audio"].get("song", {})
    if song and not song.get("licensed"):
        notes.append(f"The music '{song['title']}' by {song['artist']} is not licensed for the channel: YouTube may claim or "
                     "block the video. It is not credited in the description; replace it with royalty-free music first.")
    text = "\n".join([f"TITLE\n{yt_title}", "", "DESCRIPTION", *body, "", "TAGS", ", ".join(d["keywords"][lang]), "",
                      "NOTES (not for YouTube)", *[f"- {x}" for x in notes]]) + "\n"
    out = OUTPUT_DIR / video_id / f"description_{kind}_{lang}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out, yt_title, "\n".join(body)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--format", default="video", choices=["short", "video"])
    ap.add_argument("--lang", default="en")
    ap.add_argument("--llm", action="store_true")
    a = ap.parse_args()
    out, title, body = build(a.video_id, a.format, a.lang, a.llm)
    print("wrote", out)
