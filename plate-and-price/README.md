# Plate & Price

YouTube Shorts about easy dinners with a taste of different cuisines and the real price of each plate. The footage is
filmed by the channel owner. This folder turns one raw recording plus a few text files into two products and emails
them for approval: a **short** (captions + music) and a **video** (voice-over made from the captions + captions + music).
Project rules are in `CLAUDE.md`.

## Per-video inputs (`input/<video-id>/`)
| File | What |
|---|---|
| `raw.mp4` | the recording (its audio is the music) |
| `video.json` | which 2-4 s pieces to cut (`src_start`, `dur`, `zoom` in/out), caption style, audio, enhance settings |
| `captions_en.srt` | captions on the OUTPUT timeline, English first; `captions_es.srt` is Spanish |
| `price.json` | ingredient prices, servings; feeds the end card |
| `recipe.md` | recipe and context |
| `endcard.png` (optional) | your own end-card image; if present it replaces the generated card |

## Run it
```
cd scripts
uv run --with pillow --with imageio-ffmpeg python run_pipeline.py video-001 --lang en
```
Add `--voice` for the video with voice-over (free `edge-tts` voice, or your own `input/<id>/voice_<lang>.wav`).
Output: `output/video-001/short_en.mp4` or `video_en.mp4` (1080x1920 master) and a `_review.mp4` (about 15 MB, for email).
Both begin with a cover card (`cover_<lang>.png`, made by `make_cover.py`, with a 16:9 `thumbnail_<lang>.png`).
For a new language: `python translate_captions.py video-001 --to es` (needs an LLM key in `.env`), then run with `--lang es`.

## n8n
Import `n8n/plate-and-price-short.workflow.json` (short) and `n8n/plate-and-price-video.workflow.json` (video). Each is: Manual Trigger, Params (video id, language), Execute Command (the pipeline),
Read file, Gmail send to pablohl50@gmail.com with the review video attached. Before it works in n8n:
1. Create a Gmail OAuth2 credential and pick it in the "Email for review" node.
2. n8n 2.x disables the Execute Command node by default: remove `n8n-nodes-base.executeCommand` from `NODES_EXCLUDE`.
3. `uv` must be on the PATH of the n8n process.
The workflow file has been checked as valid JSON only; it has not been run inside n8n.

## Optional pieces
- **LLM** (`scripts/llm_client.py`): Claude or OpenAI through plain HTTPS, keys in `.env` (see `.env.example`). Used by
  `translate_captions.py`; import `complete()` anywhere else a call is needed.
- **ComfyUI** (`scripts/comfy_client.py`, `.mcp.json`): HTTP client for the local ComfyUI plus a project MCP entry for
  `comfy-mcp`, so Claude Code can run workflows in this folder. No enhancement workflow is stored yet. The built-in
  quality step is ffmpeg denoise, light sharpen and colour (`enhance` in `video.json`).
- **Brand** (`scripts/make_brand_assets.py`): icon, watermark, banner drawn locally in `brand/`; texts in `brand/channel_description.md`.

## Status and known gaps
- Tested here: `run_pipeline.py` for English and Spanish on `video-001`, with and without `--voice` (cover, captions, zoom,
  end card, music, voice timing checked with Whisper and silence detection).
- Not tested: both n8n workflows, LLM calls (no keys yet), ComfyUI enhancement.
- The song in `video-001` is "Last Train to London" by Electric Light Orchestra (found with Shazam). It is a commercial
  track: YouTube may claim or block the video. Use royalty-free music for the channel.
- Prices in `price.json` are estimates, not receipts.
- The segment times in `video.json` were picked from a contact sheet; check them in the review video.
