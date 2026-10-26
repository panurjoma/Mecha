"""Make the AI cover image of the dish for a video, if it does not exist yet.

usage: python make_cover_ai.py <video-id> [--ratio 9x16|16x9] [--confirm-paid] [--balance-usd N] [--force]
Writes input/<id>/cover_ai_9x16.png (short) and cover_ai_16x9.png (video), the files named in video.json cover.ai.
The image has NO text and no logos: make_cover.py adds the title, price and channel branding on top.

Providers (config/cover_ai.json "provider"):
  openai     - default for the next videos. The OpenAI image API makes the pixels. Needs OPENAI_API_KEY in .env; the model
               id comes from OPENAI_IMAGE_MODEL (or openai.model in the config). The owner calls the model "gpt astra 6":
               that id is UNVERIFIED, so put the exact API id in OPENAI_IMAGE_MODEL; a wrong id is reported as an API error.
               Paid: only runs with --confirm-paid.
  higgsfield - run by the assistant with the Higgsfield tools (free-plan model z_image) after it checks the credit balance.
               There is no key in .env and this script calls no API: it checks the files and prints the prompt to use.
  file       - only checks the files exist (images made by hand). Free.

Layers (directive 17): each generated image is a layer with an <image>.key sidecar (fingerprint of prompt + model +
size), the way scripts/layers.py does it. The same prompt and settings are never generated again. An image with no .key
(made by hand or with Higgsfield) is never overwritten unless --force.
Cost (directive 3): the script prints the estimated cost it knows (estimated_cost_usd.image in the config, null = unknown)
and does nothing paid without --confirm-paid. It cannot read your account balance, so check it first. With
--balance-usd N it stops if N is below a known estimate. API keys are never printed.
Not implemented: a ComfyUI workflow (needs a text-to-image checkpoint that fits the 6 GB GPU).
"""
import argparse
import base64
import json
import os
import urllib.error
import urllib.request

from common import ROOT, load_env, load_json, video_dir
from layers import digest, key_of

load_env()

RATIOS = {"9x16": "1024x1536", "16x9": "1536x1024"}


def scrub(text):
    v = os.environ.get("OPENAI_API_KEY")
    return text.replace(v, "***") if v else text


def fail_api(e):
    body = ""
    if isinstance(e, urllib.error.HTTPError):
        try:
            body = e.read().decode("utf-8", "replace")[:600]
        except Exception:
            pass
    raise SystemExit(scrub(f"OpenAI API error: {e}. {body}\nCheck OPENAI_IMAGE_MODEL (the exact API model id) and your credit."))


def model_id(cfg):
    c = cfg["openai"]
    return os.environ.get(c.get("model_env", "OPENAI_IMAGE_MODEL"), "").strip() or c["model"]


def sizes(cfg):
    return {**RATIOS, **cfg["openai"].get("sizes", {})}


def image_key(cfg, ratio, prompt):
    return digest("image", "openai", model_id(cfg), sizes(cfg)[ratio], cfg["openai"].get("quality"), prompt)


def build_prompt(meta, price, cfg, ratio):
    foods = ", ".join(i["en"].split("(")[0].strip().lower() for i in price["items"][:5])
    layout = ("empty space above and below the bowl" if ratio == "9x16"
              else "the left half of the frame is calm and empty")
    return (f"Appetizing food photograph of the finished dish: {meta['title']['en']}. Visible ingredients: {foods}. "
            f"{cfg['style']} {layout}. No text, no letters, no logos, no watermark.")


def generate_openai(prompt, ratio, cfg, out):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is not set (put it in .env)")
    body = {"model": model_id(cfg), "prompt": prompt, "size": sizes(cfg)[ratio], "n": 1}
    if cfg["openai"].get("quality"):
        body["quality"] = cfg["openai"]["quality"]
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json", "authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read())["data"][0]
        if data.get("b64_json"):
            out.write_bytes(base64.b64decode(data["b64_json"]))
        elif data.get("url"):
            with urllib.request.urlopen(data["url"], timeout=300) as r:
                out.write_bytes(r.read())
        else:
            raise SystemExit("OpenAI answered without image data")
    except (urllib.error.URLError, KeyError, ValueError) as e:
        fail_api(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--ratio", choices=list(RATIOS))
    ap.add_argument("--confirm-paid", action="store_true")
    ap.add_argument("--balance-usd", type=float, help="your checked credit; stops if below a known estimate")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    price = load_json(vdir / "price.json")
    cfg = load_json(ROOT / "config" / "cover_ai.json")
    provider = cfg["provider"]
    if provider not in ("file", "higgsfield", "openai"):
        raise SystemExit(f"unknown provider '{provider}' in config/cover_ai.json (file, higgsfield, openai)")

    jobs = []  # (ratio, out, prompt)
    for ratio in ([a.ratio] if a.ratio else RATIOS):
        out = vdir / meta["cover"]["ai"][ratio]
        keyfile = out.with_name(out.name + ".key")
        if out.exists() and not a.force:
            if not keyfile.exists():
                print("exists (no .key, made by hand or with Higgsfield, kept):", out.name)
                continue
            if provider != "openai":
                print("exists:", out.name)
                continue
            if key_of(out) == image_key(cfg, ratio, build_prompt(meta, price, cfg, ratio)):
                print("cached (same prompt and settings):", out.name)
                continue
        prompt = build_prompt(meta, price, cfg, ratio)
        if provider == "file":
            print(f"MISSING {out.name}: add the image by hand, or set provider to openai in config/cover_ai.json")
        elif provider == "higgsfield":
            print(f"MISSING {out.name}: ask the assistant to make it with Higgsfield (it checks the credit balance first). "
                  f"Prompt:\n  {prompt}")
        else:
            jobs.append((ratio, out, prompt))

    if not jobs:
        return
    est = cfg.get("estimated_cost_usd", {}).get("image")
    print(f"Paid calls planned: {len(jobs)} image(s) with model '{model_id(cfg)}' (unverified id if it is the owner's name).")
    if est is None:
        print("  Estimated cost: unknown. Read the provider's price page and fill estimated_cost_usd.image in the config.")
    else:
        total = round(est * len(jobs), 4)
        print(f"  Estimated cost: about ${total} (${est} each)")
        if a.balance_usd is not None and a.balance_usd < total:
            raise SystemExit(f"Stopped: your balance ${a.balance_usd} is below the estimate ${total}. Top up first.")
    if not a.confirm_paid:
        raise SystemExit("Stopped: this is paid. Check your credit and the estimate, then re-run with --confirm-paid "
                         "(the script cannot read your balance).")
    for ratio, out, prompt in jobs:
        generate_openai(prompt, ratio, cfg, out)
        out.with_name(out.name + ".key").write_text(image_key(cfg, ratio, prompt))
        print("wrote", out)


if __name__ == "__main__":
    main()
