# Plate & Price: project directives

Instructions for Claude (and anyone) working in this folder. Keep this file up to date; the README explains how to run things.

## The channel
YouTube channel **Plate & Price**: easy dinners with a taste of different cuisines, and the real price of each plate shown
at the end. The footage is filmed by the channel owner, nothing is AI-generated video. Tagline: "Easy dinners. Real prices."

## Directives
1. **No personal names.** Never write the names of the cooks or presenters (in files, captions, covers, descriptions,
   commit messages). The raw footage can carry a burned-in title with names in its first seconds: do not use those
   seconds (video.json starts after them; the cover card replaces the intro).
2. **Ask before acting when something is unclear** or there are several reasonable options.
3. **Check cloud credit before any paid job** (Higgsfield, RunPod, any API). The credit must cover the quoted cost; if it
   does not, or cannot be read, stop and ask the owner to top up. Free tools are preferred.
4. **Captions are English first.** Spanish (and other languages) come later as `captions_<lang>.srt`.
5. **Review by email only** (pablohl50@gmail.com) until told otherwise. Nothing is published without the owner's approval.
6. **Music:** the owner's recording carries a commercial song in video-001; flag copyright risk, prefer royalty-free.
7. **Prices are estimates** unless the owner gives receipts; label them as estimates.
8. **Never commit secrets** (`.env`, API keys, n8n credentials). Raw footage and rendered outputs stay out of git.
9. **Honest status:** say what was tested and what was not.

## Two products from the same inputs
| | Short (`short_<lang>.mp4`) | Video (`video_<lang>.mp4`) |
|---|---|---|
| Where | YouTube Shorts, vertical 9:16, about 42 s | YouTube video |
| Sound | the song | voice-over made from the captions, song lowered under it |
| Captions | burned in | burned in |
| Command | `run_pipeline.py video-001 --lang en` | `run_pipeline.py video-001 --lang en --voice` |
| n8n | `n8n/plate-and-price-short.workflow.json` | `n8n/plate-and-price-video.workflow.json` |

Both start with a cover card (real frame of the dish, title, price per serving), then 3 s zoom in/out clips, then the
price end card. The video also gets a 16:9 `thumbnail_<lang>.png`.

### Voice for the video
- Default: free text-to-speech with `edge-tts` (no key, online, sends the caption text to Microsoft's voice service).
  Voices are set per language in `video.json` ("voice").
- Your own voice: record it on the output timeline and save it as `input/<id>/voice_<lang>.wav`. It replaces the TTS file.
  A fully offline alternative is Piper (not wired in yet).

## Inputs per video (`input/<video-id>/`)
`raw.mp4`, `video.json`, `captions_<lang>.srt`, `price.json`, `recipe.md`; optional `cover.png`, `endcard.png`,
`voice_<lang>.wav` (hand-made versions win over generated ones).

## Tools and connections
- Edit: ffmpeg through `uv run --with pillow --with imageio-ffmpeg --with edge-tts python scripts/<script>.py`.
- LLM (optional): `scripts/llm_client.py` for Claude or OpenAI, keys in `.env`.
- ComfyUI (optional quality step): `scripts/comfy_client.py` and `.mcp.json` (comfy-mcp). RTX 3060 Laptop with 6 GB:
  only light models locally; heavy ones go to the cloud (see directive 3).
- Orchestration: n8n workflows in `n8n/`.
- Repo: `github.com/panurjoma/Mecha` (private). The clone lives in `_repo/` (git-ignored here); `scripts/push_to_repo.ps1 "message"` copies
  this folder into `_repo/plate-and-price/` (without raw footage, outputs, `.env`) and pushes. Push only when the owner asks.
