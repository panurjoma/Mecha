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

## Stages for a new recipe (do the least needed at each)
1. Drop the recordings in `input/<id>/` (GoPro files like `GH011564.MP4` are fine; they stay out of git).
2. Pick the moments in `video.json`: `segments` per format with `src`, `src_start`, `dur`, optional `cx` (0..1, where to crop
   sideways for a vertical short). List them in filming order.
3. Cut and join: `python cut_rough.py <id> --format short` (and `--format video`) gives `<output>/<id>/rough_<format>.mp4`
   with the clips' own sound. Check order and length before going on.
4. Clean: `python clean_footage.py <id> --format short|video` gives `<output>/<id>/clean_<format>.mp4` (settings in `video.json`
   "clean"; `shutter` in each format removes the sparkle of small reflections in 120 fps GoPro files). Then cover
   (`make_cover_ai.py`/`make_cover.py`), captions, voice, music: see the layers below.
5. Last, the bill: write `price.json` (ingredients seen in the footage, average Spanish supermarket prices, an estimate,
   same format as the first video). It makes the price end card and the price list in the video description.
The short keeps repetition to a minimum; the video can carry more secondary detail. See directive 18 in `CLAUDE.md`.

## Critic review (seven agents, Claude Opus 5.5)
Agents in `.claude/agents/`: `audience-sociologist`, `engagement-analyst`, `marketing-strategist`, `video-craft-editor`,
`audio-voice-reviewer`, `recipe-price-checker`, `discoverability-strategist`.
`python review_pack.py <id> --format short --lang en` builds what they read in `<output>/<id>/review/` (contact sheets,
facts with measured audio, the price table and recipe notes, the YouTube text and thumbnail, sheets of every recording). Run
`make_description.py` first so the discoverability reviewer has the text. In Claude Code run one agent each in parallel;
`python review_video.py <id> --format short` does the same through Claude or OpenAI (needs a key in `.env`, otherwise skipped;
it uses each agent's `model:` line). Three rounds per product; scores and fixes go in `review/history/<id>.md`.

## Hook, captions and cleaning (standard for every recipe)
- Hook: first segment with `"hook": true`, shown before the cover card (directive 21).
- Captions: `caption.en` / `caption.es` inside each segment; `make_captions.py` writes the .srt files.
- Every shot is cleaned by `clean_footage.py` before it can be used; `run_pipeline.py` runs cut, clean, captions, then the build.

## Music from an API (royalty-free, automatic)
`python pick_music.py <id>` asks the Jamendo API for an instrumental chill track that is long enough, keeps only tracks
whose Creative Commons licence allows commercial use and editing (settings in `config/music.json`), downloads it to
`input/<id>/music.mp3` and sets `audio` in `video.json`. The description then credits it with its licence link.
Needs a free `JAMENDO_CLIENT_ID` in `.env` (devportal.jamendo.com). Use `--list` to see candidates first, `--mood` and
`--start` to steer it. Tracks already used for other recipes are avoided (`music/catalog.json`). Read Jamendo's API
terms for your use; the picker's licence filter is a safeguard, not legal advice. Changing the track only rebuilds music, mix and final.

## Layers: change one thing without redoing the rest
Videos are built as layers, each a file in `<output>/<recipe>/layers/` with a `.key` fingerprint of its inputs.
Run the same command again and only the layers whose inputs changed are rebuilt (the log shows `[built]` or `[cached]`).
The only tool needed is **FFmpeg**, which the scripts already use (through `imageio-ffmpeg`, nothing to install).

| Layer (file) | Built from | Rebuilds when you change | Time |
|---|---|---|---|
| `footage_<format>.mp4` | raw video, clips, zoom, layout | clip times, zoom, layout, the raw video | slow (1-5 min), shared by all languages |
| `still_<format>_<lang>_cover/endcard.mp4` | cover and end-card images | the AI cover, the prices, the end card | seconds |
| `captioned_<format>_<lang>.mp4` | the layers above + captions | the captions file or caption style | about 30 s |
| `voice_<format>_tts_<lang>.wav` (in `input/`) | captions + voice name | the captions, the voice name or rate | seconds |
| `music_<format>.wav` | the song | the song or its start time | seconds |
| `mix_<format>_<lang>.wav` | music + voice | the voice, the music volume | seconds |
| `<format>_<lang>.mp4` (final) | captioned picture + mix | anything above (the picture is copied, not re-encoded) | seconds |
| `<format>_<lang>_review.mp4` | the final file | anything above | seconds |

Typical changes:
- **New captions:** edit `captions_<format>_<lang>.srt` and run again. The footage is reused; for the video the voice is
  regenerated from the new captions.
- **New voice:** change `voice` in `video.json` (or record your own `voice_video_<lang>.wav`) and run again. Only the voice,
  the mix and the final file are rebuilt, so the picture is not touched.
- **New song:** change `audio` in `video.json`; only the music, mix and final rebuild.
- **New language:** run with `--lang es`; the footage and the music are reused.
- **Force a rebuild:** `--force captions,mix` (layers: `footage, stills, captions, voice, music, mix, final, review`, or `all`).

The layer folder is outside git and can be deleted at any time; it will be rebuilt. It can be large (a few hundred MB).

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
