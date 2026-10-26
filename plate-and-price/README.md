# Plate & Price

YouTube channel about easy dinners with a taste of different cuisines and the real price of each plate. The footage is
filmed by the channel owner. This folder turns one raw recording plus a few text files into two products and emails
them for approval: a **short** (vertical, captions + music) and a **video** (horizontal, calm voice-over made from the
captions + captions + music). Project rules are in `CLAUDE.md`.

## Set up the channel (files to use first)
| In YouTube Studio | File |
|---|---|
| Profile picture | `brand/icon.png` (1024x1024) |
| Banner | `brand/banner.png` (2560x1440, content inside the centre safe area) |
| Video watermark (Customization > Branding) | `brand/watermark.png` (512x512, white on transparent) |
| Channel name, description, keywords | `brand/channel_description.md` (English and Spanish) |
| First short | `<output>/<recipe>/short_en.mp4` |
| First video | `<output>/<recipe>/video_en.mp4` plus thumbnail `input/<recipe>/thumbnail_en.png` |

`<output>` is the rendered-videos folder: `plate-and-price/output/` next to this clone. Check the captions and the
estimated prices in the review videos before uploading. The song in the first recording is commercial (see below).

## Per-video inputs (`input/<recipe-name>/`)
| File | What |
|---|---|
| `raw.mp4` | the recording (its audio is the music); git-ignored |
| `video.json` | per format (`short`, `video`): size, clips (`src_start`, `dur`, `zoom`), cover and end card length, caption file and style |
| `captions_short_en.srt`, `captions_video_en.srt` | captions on each product's timeline; the Spanish ones end in `_es.srt` |
| `price.json` | ingredient prices and servings; feeds the end card and the cover |
| `recipe.md` | recipe and context |
| `cover_ai_9x16.png`, `cover_ai_16x9.png` | the AI-generated dish images (no text) used by the covers |
| `endcard_<format>.png`, `cover_<format>.png` (optional) | hand-made images that replace the generated ones |
| `voice_video_<lang>.wav` (optional) | your own voice on the video timeline, replaces the generated voice |

## Run it
```
cd scripts
uv run --with pillow --with imageio-ffmpeg --with edge-tts python run_pipeline.py <recipe-name> --format short --lang en
uv run --with pillow --with imageio-ffmpeg --with edge-tts python run_pipeline.py <recipe-name> --format video --lang en
```
Output (in `PLATE_OUTPUT_DIR`, see `.env.example`): `<format>_<lang>.mp4` and a smaller `_review.mp4` for email.
The video takes several minutes to render (1080p, slow preset). For a new language, run
`python translate_captions.py <recipe-name> --format video --to es` (needs an LLM key in `.env`), then run with `--lang es`.

## YouTube title, description and tags
`run_pipeline.py` also writes `description_<format>_<lang>.md` next to each video: TITLE, DESCRIPTION, TAGS and a NOTES
section for you (not for YouTube). English by default; `--lang es` writes the Spanish one. You can run it alone:
`python make_description.py <recipe-name> --format video --lang en`.
- **Short:** a title ending in #Shorts, a two-line hook, the cost per serving and hashtags.
- **Video:** hook, the estimated price list and total, chapters, a closing line and hashtags. Chapters come from
  `formats.video.chapters` in `video.json` (they must start at 0:00, be at least three, and last at least 10 s each).
- The hook, closing line, keywords and hashtags are in `video.json` under `description`. Add `--llm` to have Claude or
  OpenAI rewrite the hook in the same close tone (needs a key in `.env`; not tested yet).
- The text is also placed in the review email by both n8n workflows.
- The music is never credited unless `audio.song.licensed` is true.

## Tone and voices
Captions, narration and descriptions are written in a close, natural tone (see directives 14 and 15 in `CLAUDE.md`).
The voice-over is always a male voice: `en-US-BrianMultilingualNeural` (English, casual and approachable) and
`es-ES-AlvaroNeural` (Spanish, friendly) from the free edge-tts service, set in `video.json` under `voice`. Other male
options: `en-US-AndrewMultilingualNeural` (warm, confident), `en-US-GuyNeural`, `es-MX-JorgeNeural`. List them all with `edge-tts --list-voices`. For the most natural result, record your own voice as
`input/<recipe-name>/voice_video_<lang>.wav`.

## The AI cover
Every product opens with a cover card: an AI image of the finished dish with the channel branding on top.
- The image files are named in `video.json` (`cover.ai`). `make_cover_ai.py` reports when one is missing.
- Provider is set in `config/cover_ai.json`: `file` (add the image by hand or have Claude generate it) or `openai`
  (paid, runs only with `--confirm-paid` after you check your credit).
- The first covers were generated with Higgsfield `z_image`, the only image model the free plan allows.
- `make_cover.py` adds the title, price per serving and channel name. The same 16:9 cover is the YouTube thumbnail.

## n8n
Import `n8n/plate-and-price-short.workflow.json` and `n8n/plate-and-price-video.workflow.json`. Each is: Manual Trigger,
Params (recipe folder, language, project path), Execute Command (the pipeline), Read file, Gmail send to
pablohl50@gmail.com with the review video attached. Before it works in n8n:
1. Create a Gmail OAuth2 credential and pick it in the "Email for review" node.
2. n8n 2.x disables the Execute Command node by default: remove `n8n-nodes-base.executeCommand` from `NODES_EXCLUDE`.
3. `uv` must be on the PATH of the n8n process, and `PLATE_OUTPUT_DIR` in `.env` must point to the output folder two levels above this one.
4. The video review file is about 20 MB; Gmail's limit is 25 MB.
The workflow files are valid JSON but have not been run inside n8n.

## Optional pieces
- **LLM** (`scripts/llm_client.py`): Claude or OpenAI through plain HTTPS, keys in `.env`. Used by `translate_captions.py`.
- **ComfyUI** (`scripts/comfy_client.py`, `.mcp.json`): HTTP client for the local ComfyUI plus a project MCP entry for
  `comfy-mcp`. No enhancement workflow is stored yet; the built-in quality step is ffmpeg denoise, light sharpen and colour.
- **Brand** (`scripts/make_brand_assets.py`): icon, watermark and banner drawn locally in `brand/`.

## Git
This folder is `plate-and-price/` inside a clone of `github.com/panurjoma/Mecha`, branch `feat/plate-and-price`.
Commit and push from here: `git add -A && git commit -m "..." && git push`.

## Status and known gaps
- Tested here: the short and the video for the first recipe in English (render, cover, captions, zoom, end card, music, voice).
- Not tested: the Spanish video after the format split, both n8n workflows, LLM calls (no keys yet), ComfyUI enhancement.
- The song in the first recording is "Last Train to London" by Electric Light Orchestra (found with Shazam). It is a
  commercial track: YouTube may claim or block the video. Use royalty-free music for the channel.
- Prices in `price.json` are estimates, not receipts.
- The clip times in `video.json` were picked from a contact sheet; check them in the review videos.
- The free voice service (edge-tts) sometimes returns no audio; `make_voice.py` retries up to four times.
