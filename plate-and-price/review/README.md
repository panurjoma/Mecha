# Reviewer agents

Codex equivalents of all seven roles are in `../.codex/agents/*.toml`; see [codex.md](codex.md) for usage.
Every round checks the caption preference in CLAUDE.md directive 25: slightly larger, high-contrast brand-colour
captions, checked in English and Spanish with the food and phone controls visible. Flag small text, weak contrast,
long lines and captions covering the action; use `[captions]` fixes to address them.

Seven agents in `../.claude/agents/` (model `claude-opus-5-5`) judge a finished short or video:

| Agent | Lens | Special evidence |
|---|---|---|
| `audience-sociologist` | who watches, trust, social meaning, comprehension without sound, accessibility | sheets, captions |
| `engagement-analyst` | hook, retention curve, pacing, safe area, loop, end | sheets, facts |
| `marketing-strategist` | promise, brand consistency, price moment, calls to action | sheets, cover |
| `video-craft-editor` | recipe continuity, perspective, hero shots, cuts, picture clean-up | source-clip sheets |
| `audio-voice-reviewer` | loudness, voice-over pacing and naturalness, music balance | measured LUFS, levels, chars/s per voice line |
| `recipe-price-checker` | steps, claims, quantities, the Spanish price estimate | price table, recipe.md |
| `discoverability-strategist` | title, description, tags, chapters, thumbnail, search intent (EN and ES) | description file, thumbnail |

They read the files from `scripts/review_pack.py` and each answers with `SCORE: x/10`, problems, a hook suggestion and
numbered fixes. Process: three rounds per product. After each round the producer applies the fixes that make sense,
rebuilds only the layers that change (directive 17), regenerates the pack and asks again. Scores and what changed are
recorded in `history/<recipe>.md`. The agents never change files themselves. Compliance and licensing is not a critic.
In Claude Code they run as parallel agents; for n8n `scripts/review_video.py` runs them through an LLM key.

## Every agent changes the final video
Each agent has levers, the places where its opinion lands. Every fix it proposes starts with its lever in brackets.

| Lever | What it changes | Agents that use it |
|---|---|---|
| `[captions]` | caption text and timing, the voice script (`segments[].caption`, `cover_caption`, `end_caption`) | all seven agents |
| `[shots]` | which clips, order, length, speed (`segments[].speed`: speed up a slow moment such as chopping), the hook, the ending (`segments`) | sociologist, engagement, marketing, craft, recipe-price |
| `[picture]` | clean-up, grade, framing, layout (`clean`, per-clip `layout`, `cx`) | craft |
| `[audio]` | music choice and level, voice pacing, loudness (`audio`, voice settings) | audio-voice, engagement, craft |
| `[text]` | description, tags, chapters, thumbnail; the title only with the owner's approval | discoverability, sociologist, marketing, recipe-price |
| `[price]` | `price.json` lines and notes, the price end card | recipe-price, marketing, sociologist |
| `[cover]` | cover card and end card design | marketing, engagement, sociologist, discoverability |

Rules: all seven are consulted every round; each fix is applied or declined with a reason; conflicts are settled by the
owner's fixed rules first, then the fix several agents agree on, then the most serious problem.

### Decision log (copy into `history/<recipe>.md` after each round)
| Round | Agent | Fix (lever) | Decision | Reason or where it landed |
|---|---|---|---|---|
| 1 | engagement-analyst | [shots] cut the second onion shot | applied | segments, short |
| 1 | marketing-strategist | [cover] remove the cover card | declined | owner rule |

## Which agents review each language
Only agents whose judgment changes with the language are run for English and Spanish separately; the others review the shared
cut once. The setting is `language:` in each agent file.

| Agent | `language:` | Why |
|---|---|---|
| audience-sociologist | separate | tone, naturalness and cultural fit of captions, cover and end card |
| marketing-strategist | separate | promise, tagline, cover and end-card wording per language |
| recipe-price-checker | separate | ingredient names, units, price format (4,85 EUR) per language |
| discoverability-strategist | separate | title, description, tags, search terms per language |
| audio-voice-reviewer | separate-if-voice | the voice-over speed and script differ by language; a short without a voice-over is the same in both (since directive 26 shorts have a voice, so they are reviewed per language) |
| engagement-analyst | shared | hook, pacing, retention are the same cut in both languages |
| video-craft-editor | shared | continuity, perspective, picture quality are the same picture |

A shared agent's score applies to both languages of the product. So per product there are 4 language-specific agents (plus
the audio-voice agent when there is a voice) with two scores each, and 2 or 3 agents with one score.
