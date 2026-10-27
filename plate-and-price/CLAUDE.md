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
       Do the timing analysis here: a slow moment (chopping an onion or garlic, waiting, stirring) is sped up with
       `segments[].speed` (1.5 to 2 is natural; `dur` stays the seconds on screen, the clip is read for `dur * speed`
       source seconds) so it takes fewer seconds and the dinner feels quick. Never speed up a moment that carries a
       key action (the pour, the plate) or whose sound or detail matters; the critics may add or remove speed-ups.
       Short: about 2-3 s per moment; its length has no fixed limit (directive 28). Video: about 6 s per moment, about 90 s.
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
    6. **Critics** (seven agents, two rounds, directive 19), then the final file and YouTube text.
    The short repeats as little as possible (one idea per moment, short captions, and a calm voice-over that reads them, directive 26). The video may add secondary
    details (extra moments, a fuller explanation, voice-over). Never redo an earlier stage to change a later one.

19. **Seven critics, two rounds.** Before a short or video is final, seven reviewer agents judge it from different
    perspectives (`.claude/agents/`, all set to Claude Opus 5.5): `audience-sociologist` (who watches, trust, social
    meaning, accessibility), `engagement-analyst` (hook, retention, pacing, loop), `marketing-strategist` (promise, brand,
    price moment, calls to action), `video-craft-editor` (recipe continuity, perspective, hero shots, picture craft),
    `audio-voice-reviewer` (measured loudness, voice-over pacing and naturalness, music balance), `recipe-price-checker`
    (steps, claims and the Spanish price estimate) and `discoverability-strategist` (title, description, tags, thumbnail,
    search habits). They read the evidence made by `scripts/review_pack.py` (contact sheets, caption timeline, facts, measured
    audio, price table, YouTube text, thumbnail, sheets of every recording) and each answers with `SCORE: x/10`, problems,
    a hook suggestion and numbered fixes. Run two rounds per product (short and video; the owner reduced it from three): apply the fixes that make sense,
    rebuild, review again, and keep the scores in `review/history/<id>.md`. The owner can allow a product to grow when the
    critics ask for it. In n8n `scripts/review_video.py` runs the same agents through an LLM key. Compliance and licensing
    is deliberately not a critic; the owner decides about music rights.
20. **Every shot that goes into an official short or video is cleaned first.** Glare, small flickering highlights,
    blown whites, colour cast and noise are removed by the clean stage (`scripts/clean_footage.py`) for every shot, including a
    shot added later and the hook. `run_pipeline.py` always runs `cut_rough.py` then `clean_footage.py` before it builds
    anything, so an uncleaned shot can never reach a final file. Never use a frame straight from the recordings.
21. **A moving hook opens every product.** The first 1-2 s show an appetizing moving shot (a clip repeated later: cheese
    falling, a pour, a glossy stir) before the cover card. It is the first segment of `segments` with `"hook": true`.
    Captions live in the segments (`caption.en`, `caption.es`) and `make_captions.py` places them, so adding or retiming a
    clip never needs hand-edited caption files.

22. **Images from an API: one provider per situation, paid only with a check.** Covers, thumbnails and brand images are made
    in one of two ways. For now the assistant uses the Higgsfield tools (free-plan model z_image) after checking the credit
    balance (provider `higgsfield`, no key in `.env`). For the next videos the only image provider is the OpenAI
    subscription (provider `openai`, `OPENAI_API_KEY` in `.env`, run by `scripts/make_cover_ai.py`). The exact model id goes
    in `OPENAI_IMAGE_MODEL`; the owner calls it "gpt astra 6" and that id is unverified, so a wrong id shows as an API error,
    never a guess, and model names stay in config and `.env`, not hardcoded as facts. The Claude subscription is not used to
    make images. Every image obeys directives 3, 8, 10 and 17: no text or logos inside the image, a paid call only after the
    credit and the estimated cost are checked (the script prints the estimate and needs `--confirm-paid`), keys only in
    `.env` and never printed, and the image is a cached layer with a `.key` that is not regenerated when the prompt and
    settings are the same.

23. **The final folder.** Each recipe's approved shorts and videos live in `<output>/<id>/final/`: `short_<lang>.mp4`,
    `video_<lang>.mp4`, their `description_<format>_<lang>.md` and the `thumbnail_<lang>.png`. Only finished versions go
    there. When a version is improved, the same files are updated in place: the build moves the old file (and its fingerprint)
    out of `final/` into `<output>/<id>/archive/` with a time stamp, then puts the new one in `final/`, so `final/` always holds
    exactly the current version of each product. The small email copies go to `<output>/<id>/email/`, the intermediate layers
    stay in `layers/`, and the critics' evidence in `review/`. Never leave work-in-progress or duplicate versions in `final/`.

24. **Every critic shapes the final video.** All seven agents (directive 19) give an opinion every time a short or video is
    generated, and none is skipped. Each opinion has a place where it changes the result: `audience-sociologist` and
    `engagement-analyst` change captions, shot selection and order, the hook and the cover length; `marketing-strategist` changes
    the cover, captions, price moment and calls to action; `video-craft-editor` changes shots, picture clean-up and framing;
    `audio-voice-reviewer` changes music level, loudness and the voice script; `recipe-price-checker` changes the steps in the
    captions and the prices (`price.json`); `discoverability-strategist` changes the description, tags, chapters, thumbnail and
    the keywords in the captions (the title stays the dish name and changes only with the owner's approval). Every fix is tagged
    with its lever (`[captions]`, `[shots]`, `[picture]`, `[audio]`, `[text]`, `[price]`, `[cover]`) and, after each round, is either
    applied or declined with a reason in `review/history/<id>.md` (a decision log per agent). Conflicts are settled in this order:
    the owner's fixed rules, then the fix several agents agree on, then the most serious problem. No product is final until all
    seven were consulted, their fixes decided, and the changed layers rebuilt. `run_pipeline.py` reminds you of this at the end.
    Language split: agents whose judgment depends on the language (sociologist, marketing, recipe-price, discoverability, and
    audio-voice when there is a voice-over) review English and Spanish separately; engagement, craft and audio-voice on a
    short without a voice-over review the shared cut once (`language:` in each agent file, table in `review/README.md`).

25. **Captions must be easy to read.** Burned-in captions are large, warm yellow (`color` FFE27A) with a dark outline, and on the
    video a soft dark box behind the text. Defaults: short size 92, outline 7, in the top third (align 8, margin_v 250, clear of
    the app buttons at the bottom and the right edge); video size 74, outline 9, box, bottom centre a little above the edge
    (margin_v 85). They are set per format in `video.json` under `caption_style` (`size`, `outline`, `color`, `box`, `margin_v`, `align`).
    Keep lines short (two lines at most, about 22 characters per line on the short) and off the key action. Change the style
    only when the critics ask for a legibility improvement; only the captioned layer and the final file rebuild. Keep all text above the
    bottom 20 %, avoid relying on colour alone for meaning, check long lines and accented characters (Ñ, é) after every caption
    change by looking at rendered English and Spanish frames, and have every critic round check caption colour, size, contrast and placement.

26. **Both products carry the voice.** The short and the video both have the calm male voice-over (`voice: true` in both
    formats), made from the captions, so the viewer can listen and read at the same time instead of only reading. Each short
    moment is long enough for its spoken line (about 1.7 s for two words, 2.2 s for a short sentence), lines are short, the
    voice is never sped up (`tempo_max` 1.0 in the short), and the song sits lower under it (`volume_with_voice`). The voice
    layer trims the silence edge-tts adds to each line before measuring it, and warns when a line is longer than its window.
    Spanish and English are reviewed separately for both products because the voice differs by language.

27. **The vertical crop does not have to be the centre.** The recordings are horizontal (1920x1080) and the short is vertical, so
    each short moment shows a vertical slice of the frame. `segments[].cx` (0 = left edge, 0.5 = centre, 1 = right edge) chooses
    that slice per moment, and it must be chosen on purpose, not left at 0.5: look at where the action is (the knife, the pan, the
    plate, the hands) and shift the crop left or right to keep it, and any key detail such as a bottle or an ingredient, inside the
    frame. A moment whose action is wider than the slice may use `"layout": "blurpad"` (whole width over a blurred copy).
    Check this at the selection stage and in every critic round (the `[picture]` lever covers `cx` and `layout`); a change only
    rebuilds the footage layer and what depends on it. The horizontal video shows the whole width and is not affected.

28. **No length limit for the short.** A short is as long as it takes to show every important step of the recipe clearly; it may
    pass a minute. The old 35-40 s target is gone. What limits the length is clarity, not a clock: every key step (each
    ingredient or action the dish depends on) must be visible and understandable, and every moment must earn its seconds, so slow
    moments are sped up (`segments[].speed`, directive 18) or trimmed rather than dropping a key step. Voice lines keep their windows
    (directive 26). The critics must not mark a short down for being long, only for steps that are unclear, missing or dragging.

29. **Crop anything that should not be seen, in both formats.** The whole camera frame does not have to appear. In the horizontal
    video too, a moment can be cropped and tightened so that something unwanted stays out (a name, clutter, a person, a messy
    corner, the edge of the counter, an ingredient that does not belong in this recipe): `segments[].crop` is a zoom factor (1 = whole
    frame, 1.25 = the central 80 %, 1.5 = the central two thirds) and `cx`/`cy` (0 to 1, default 0.5) say which part of the picture
    is kept (0 = left/top edge, 1 = right/bottom edge); the short uses `cx` the same way (directive 27). Decide it at the selection
    stage and in every critic round (`[picture]` lever). Keep the crop modest (about 1.5 at most on 1080p footage, to stay sharp),
    and prefer a different moment over a heavy crop if the unwanted thing cannot be cropped out. A crop only rebuilds the footage
    layer and what depends on it. `"layout": "blurpad"` ignores `crop`.

## Two products from the same inputs
| | Short (`short_<lang>.mp4`) | Video (`video_<lang>.mp4`) |
|---|---|---|
| Where | YouTube Shorts | YouTube channel |
| Size | 1080x1920, vertical, as long as the recipe needs (30 s to over a minute) | 1920x1080, horizontal, about 80-90 s |
| Sound | calm voice-over made from the captions, song lowered under it | calm voice-over made from the captions, song lowered under it |
| Captions | burned in (short phrases, top of frame) | burned in (full sentences, bottom of frame) |
| Cover | 1.5 s, AI image 9:16 | 3 s, AI image 16:9 (also the thumbnail) |
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
- AI cover: `scripts/make_cover_ai.py` (provider in `config/cover_ai.json`: `openai` for next videos, paid, only with
  `--confirm-paid`; `higgsfield` run by the assistant; `file`; see directive 22).
  The first cover was made with Higgsfield z_image (the only image model the free plan allows).
- LLM (optional): `scripts/llm_client.py` for Claude or OpenAI, keys in `.env`.
- ComfyUI (optional quality step): `scripts/comfy_client.py` and `.mcp.json` (comfy-mcp). RTX 3060 Laptop with 6 GB:
  only light models locally; heavy ones go to the cloud (see directive 3).
- Orchestration: n8n workflows in `n8n/`.
- Repo: `github.com/panurjoma/Mecha` (private), folder `plate-and-price/`, branch `feat/plate-and-price`. Work and commit
  directly in this folder with git. Push only when the owner asks.
