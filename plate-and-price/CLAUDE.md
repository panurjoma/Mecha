# Plate & Price: project directives

Instructions for Claude (and anyone) working in this folder. Keep this file up to date; the README explains how to run things.

## The channel
YouTube channel **Plate & Price**: easy dinners with a taste of different cuisines, and the real price of each plate shown
at the end. The footage is filmed by the channel owner; only the cover image is AI-generated. Tagline: "Easy dinners. Real prices."

## Directives
1. **No personal names.** Never write the names of the cooks or presenters (in files, captions, covers, descriptions,
   commit messages). The raw footage can carry a burned-in title with names in its first seconds: do not use those
   seconds (video.json starts after them; the cover card replaces the intro).
2. **Ask before acting when something is unclear** or there are several reasonable options.
3. **Check cloud credit before any paid job** (Higgsfield, RunPod, OpenAI, any API). The credit must cover the quoted
   cost; if it does not, or cannot be read, stop and ask the owner to top up. Free tools are preferred.
4. **Captions are English first.** Spanish (and other languages) come later as separate caption files.
5. **Review by email only** (pablohl50@gmail.com) until told otherwise. Nothing is published without the owner's approval.
6. **Music:** the owner's recording carries a commercial song in the first video; flag copyright risk, prefer royalty-free.
7. **Prices are estimates** unless the owner gives receipts; label them as estimates.
8. **Never commit secrets** (`.env`, API keys, n8n credentials). Raw footage, voice files and rendered videos stay out of git.
9. **Honest status:** say what was tested and what was not.
10. **AI cover first.** Every video starts with a cover card built on a pure AI-generated image of the finished dish
    (no text inside the image), in the channel colours (tomato red, cream, charcoal), with the title, price per serving and
    channel name added on top. Never use a frame of the footage as the cover. The cover lasts 2 s in the short and 3 s in the video.
11. **The video's voice is never rushed.** Narration is calm: slower voice rate, one sentence per 6 s window, speed raised
    at most 8 % (`tempo_max`). If a sentence does not fit its window, shorten the sentence, do not speed up the voice.
12. **Two formats, two sizes.** Shorts are vertical 1080x1920 for phones. The YouTube video is horizontal 1920x1080
    (footage centred over a blurred copy), longer clips, voice-over, bigger pauses. Never reuse one file for both.
13. **One copy of every file.** This folder is a clone of the repo, so there are no duplicates. Only rendered videos live
    outside git (in `plate-and-price/output/`, set by `PLATE_OUTPUT_DIR` in `.env`), plus raw footage and voice `.wav` files.

14. **Natural voices, never robotic.** The voice-over uses the most conversational neural voices available (a male voice in both languages:
    Brian for English, Álvaro for Spanish, both set in `video.json` "voice"; do not switch to a female voice), slightly slowed, reading sentences written to be spoken. If a voice
    sounds stiff, change the voice name or the wording, not the speed. Your own recorded voice always wins.
15. **Close, natural tone everywhere.** Captions, voice script and descriptions sound like a friend talking in the kitchen:
    second person, contractions, short sentences, warm and direct, no corporate or marketing phrases, no emojis.
16. **Every product gets its YouTube text.** The pipeline writes a title, description and tags for each short and video
    (`description_<format>_<lang>.md`), English by default, Spanish with `--lang es`. The video description has the
    price list, chapters (from `video.json`) and hashtags; the short's is brief. The text is also in the review email.
    Never credit music in the description unless it is licensed for the channel.

17. **Layered generation, always.** A video is never rendered in one go. It is built from separate layers that are cached
    (`scripts/layers.py`): footage, cover and end-card clips, captions burned onto the picture, music, voice, mix, final.
    Changing the captions, the voice, the song, the cover or the clips rebuilds only the layers that depend on it, so the
    owner can change one thing and re-upload quickly. Any new script or step must follow this: produce its output as a
    cached layer with a fingerprint of its inputs, never overwrite another layer's file, and never re-render the footage
    just to change text or sound. Run with `--force <layer>` only when a rebuild is really needed.

18. **Work in stages, doing the least needed at each one.** A product goes through these stages in order, each one a cached
    layer, and a stage is only started when the owner has seen the previous one:
    1. **Select**: pick the moments from the recordings (several files are normal; `segments[].src`, `src_start`, `dur`).
       Short: about 3 s per moment, about 35 s in total with the cover and end card. Video: about 6 s per moment, about 90 s.
    2. **Cut and join** (`cut_rough.py`): put the moments together in filming order (file name and modified time agree)
       with the clips' own sound. Nothing else yet: no cover, captions, music or cleaning.
    3. **Clean** (`clean_footage.py`, settings in `video.json` "clean"): only after the order and length are agreed. Sparkle from
       small bright reflections is cut at stage 2 with `shutter` (blends 120 fps frames); stage 3 adds denoise, tamed highlights,
       white balance, colour and light sharpening.
    4. **Cover**, then **captions** (English first, Spanish second), then **voice** (video only) and **music**
       (chosen by the owner, or picked by `pick_music.py` from the Jamendo API; always royalty-free, never a commercial song).
    5. **Bill and price estimate**, last: list the ingredients seen in the footage in `input/<id>/price.json` (same format as
       the first video: items in English and Spanish, price, servings) using average Spanish supermarket prices, labelled as
       an estimate. It feeds the price end card (`make_endcard.py`) and the video description's price list.
    6. **Critics** (four agents, three rounds, directive 19), then the final file and YouTube text.
    The short repeats as little as possible (one idea per moment, short captions, no voice). The video may add secondary
    details (extra moments, a fuller explanation, voice-over). Never redo an earlier stage to change a later one.

19. **Four critics, three rounds.** Before a short or video is final, four reviewer agents judge it from different
    perspectives (`.claude/agents/`): `audience-sociologist` (who watches, trust, social meaning, accessibility),
    `engagement-analyst` (hook, retention, pacing, loop), `marketing-strategist` (promise, brand, price moment, calls to
    action) and `video-craft-editor` (recipe continuity, camera perspective, hero shots, picture and audio craft). They read
    the evidence made by `scripts/review_pack.py` (contact sheets, caption timeline, facts, sheets of every recording) and each
    answers with `SCORE: x/10`, problems, a hook suggestion and numbered fixes. Run three rounds per product (short and
    video): apply the fixes that make sense, rebuild, review again, and keep the scores in `review/history/<id>.md` so the
    progression is visible. The owner can allow a product to grow when the critics ask for it. Judge against what real viewers
    and the platform reward now. In n8n `scripts/review_video.py` runs the same four agents through an LLM key.
20. **Every shot that goes into an official short or video is cleaned first.** Glare, small flickering highlights,
    blown whites, colour cast and noise are removed by the clean stage (`scripts/clean_footage.py`) for every shot, including a
    shot added later and the hook. `run_pipeline.py` always runs `cut_rough.py` then `clean_footage.py` before it builds
    anything, so an uncleaned shot can never reach a final file. Never use a frame straight from the recordings.
21. **A moving hook opens every product.** The first 1-2 s show an appetizing moving shot (a clip repeated later: cheese
    falling, a pour, a glossy stir) before the cover card. It is the first segment of `segments` with `"hook": true`.
    Captions live in the segments (`caption.en`, `caption.es`) and `make_captions.py` places them, so adding or retiming a
    clip never needs hand-edited caption files.

## Two products from the same inputs
| | Short (`short_<lang>.mp4`) | Video (`video_<lang>.mp4`) |
|---|---|---|
| Where | YouTube Shorts | YouTube channel |
| Size | 1080x1920, vertical, about 41 s | 1920x1080, horizontal, about 81 s |
| Sound | the song | calm voice-over made from the captions, song lowered under it |
| Captions | burned in (short phrases, top of frame) | burned in (full sentences, bottom of frame) |
| Cover | 2 s, AI image 9:16 | 3 s, AI image 16:9 (also the thumbnail) |
| Command | `run_pipeline.py <id> --format short --lang en` | `run_pipeline.py <id> --format video --lang en` |
| n8n | `n8n/plate-and-price-short.workflow.json` | `n8n/plate-and-price-video.workflow.json` |

All settings (segments, durations, caption files, styles) are in `input/<id>/video.json` under `formats`.

### Voice for the video
- Default: free text-to-speech with `edge-tts` (no key, online, sends the caption text to Microsoft's voice service).
  Voices and rate are set per language in `video.json` ("voice").
- Your own voice: record it on the video timeline and save it as `input/<id>/voice_video_<lang>.wav`. It replaces the TTS file.
  A fully offline alternative is Piper (not wired in yet).

## Inputs per video (`input/<video-id>/`, folder named after the recipe)
`raw.mp4`, `video.json`, `captions_<format>_<lang>.srt`, `price.json`, `recipe.md`, the AI covers `cover_ai_9x16.png` and
`cover_ai_16x9.png`; optional hand-made `cover_<format>.png`, `endcard_<format>.png`, `voice_video_<lang>.wav` (hand-made
versions win over generated ones).

## Tools and connections
- Edit: ffmpeg through `uv run --with pillow --with imageio-ffmpeg --with edge-tts python scripts/<script>.py`.
- AI cover: `scripts/make_cover_ai.py` (provider in `config/cover_ai.json`: `file` or paid `openai`, only with `--confirm-paid`).
  The first cover was made with Higgsfield z_image (the only image model the free plan allows).
- LLM (optional): `scripts/llm_client.py` for Claude or OpenAI, keys in `.env`.
- ComfyUI (optional quality step): `scripts/comfy_client.py` and `.mcp.json` (comfy-mcp). RTX 3060 Laptop with 6 GB:
  only light models locally; heavy ones go to the cloud (see directive 3).
- Orchestration: n8n workflows in `n8n/`.
- Repo: `github.com/panurjoma/Mecha` (private), folder `plate-and-price/`, branch `feat/plate-and-price`. Work and commit
  directly in this folder with git. Push only when the owner asks.
