# Reviewer agents

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
| `[shots]` | which clips, order, length, the hook, the ending (`segments`) | sociologist, engagement, marketing, craft, recipe-price |
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
