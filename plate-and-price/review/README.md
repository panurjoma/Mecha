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
