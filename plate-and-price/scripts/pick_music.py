"""Pick a royalty-free track for a recipe through the Jamendo API and set it up in video.json.

usage: python pick_music.py <video-id> [--mood chillout,lounge] [--start 0] [--list] [--dry-run]
Needs JAMENDO_CLIENT_ID in .env (free key from devportal.jamendo.com). Settings: config/music.json.
What it does:
  1. asks Jamendo for instrumental tracks with the moods and speed in config/music.json, long enough for the video;
  2. keeps only tracks that can be downloaded and whose licence allows commercial use and editing (see config);
  3. prefers tracks not used for other recipes (music/catalog.json) and takes the best-ranked one;
  4. downloads it to input/<id>/music.mp3 (git-ignored) and records it in music/catalog.json;
  5. sets video.json "audio" (source, start, song with licensed=true, licence URL) so the layers pick it up.
The description credits the track from that record (see make_description.py). Changing the track later only rebuilds
the music, mix and final layers. --list shows the candidates without downloading anything.
"""
import argparse
import json
import os
import urllib.parse
import urllib.request

from common import ROOT, load_json, video_dir

API = "https://api.jamendo.com/v3.0/tracks/"


def fetch_candidates(cfg, moods, client_id, limit=50):
    q = {"client_id": client_id, "format": "json", "limit": limit, "include": "licenses", "order": "popularity_month",
         "fuzzytags": "+".join(moods), "speed": "+".join(cfg["speed"]), "audioformat": "mp32",
         "durationbetween": f"{cfg['min_length_s']}_600"}
    if cfg.get("vocalinstrumental"):
        q["vocalinstrumental"] = cfg["vocalinstrumental"]
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "plate-and-price/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("headers", {}).get("status") != "success":
        raise SystemExit(f"Jamendo error: {data.get('headers')}")
    return data["results"]


def usable(track, cfg):
    """Downloadable, long enough, and with a licence that allows commercial use and editing."""
    url = track.get("license_ccurl", "")
    return bool(track.get("audiodownload")) and track.get("duration", 0) >= cfg["min_length_s"] \
        and any(a in url for a in cfg["allowed_licenses"])


def choose(tracks, cfg, used_ids):
    """Usable tracks, those not used for another recipe first (ranking from the API is kept)."""
    ok = [t for t in tracks if usable(t, cfg)]
    return [t for t in ok if str(t["id"]) not in used_ids] + [t for t in ok if str(t["id"]) in used_ids]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video_id")
    ap.add_argument("--mood", help="comma list of Jamendo tags, overrides config/music.json")
    ap.add_argument("--start", type=float, default=0.0, help="seconds into the track where the video should start")
    ap.add_argument("--list", action="store_true", help="show candidates and stop")
    ap.add_argument("--dry-run", action="store_true", help="choose but do not download or change video.json")
    a = ap.parse_args()
    cfg = load_json(ROOT / "config" / "music.json")
    cid = os.environ.get("JAMENDO_CLIENT_ID")
    if not cid:
        raise SystemExit("JAMENDO_CLIENT_ID is not set. Create a free account at https://devportal.jamendo.com, copy the "
                         "client id into .env (see .env.example), then run this again.")
    vdir = video_dir(a.video_id)
    meta = load_json(vdir / "video.json")
    moods = a.mood.split(",") if a.mood else sorted({m for f in cfg["moods"].values() for m in f})
    catalog_path = ROOT / "music" / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"tracks": []}
    used = {str(t["id"]) for t in catalog["tracks"] if t.get("recipe") != a.video_id}
    pool = choose(fetch_candidates(cfg, moods, cid), cfg, used)
    if not pool:
        raise SystemExit("no usable track found (none downloadable with a commercial-use licence): try other --mood tags")
    for t in pool[:8]:
        print(f"{t['id']:>9}  {t['duration']:>3}s  {t['artist_name']} - {t['name']}  {t['license_ccurl']}")
    if a.list or a.dry_run:
        return
    t = pool[0]
    dest = vdir / "music.mp3"
    req = urllib.request.Request(t["audiodownload"], headers={"User-Agent": "plate-and-price/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as out:
        out.write(r.read())
    entry = {"id": t["id"], "title": t["name"], "artist": t["artist_name"], "url": t.get("shareurl", ""),
             "license_url": t["license_ccurl"], "duration": t["duration"], "recipe": a.video_id, "source": "jamendo"}
    catalog["tracks"] = [x for x in catalog["tracks"] if x.get("recipe") != a.video_id] + [entry]
    catalog_path.parent.mkdir(exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    au = meta.setdefault("audio", {})
    au.update({"source": "music.mp3", "start": a.start,
               "song": {"title": t["name"], "artist": t["artist_name"], "licensed": True, "license_url": t["license_ccurl"],
                        "source_url": t.get("shareurl", ""), "attribution_required": True}})
    (vdir / "video.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"picked: {t['artist_name']} - {t['name']} ({t['license_ccurl']}); saved {dest}")


if __name__ == "__main__":
    main()
