# Reviewer agents

Four agents in `../.claude/agents/` judge a finished short or video from different perspectives:

| Agent | Lens |
|---|---|
| `audience-sociologist` | who watches, trust, social meaning, comprehension without sound, accessibility |
| `engagement-analyst` | hook, retention curve, pacing, safe area, loop, end |
| `marketing-strategist` | promise, brand consistency, price moment, calls to action, packaging |
| `video-craft-editor` | recipe continuity, perspective, hero shots, cuts, picture clean-up, audio craft |

They read the evidence from `scripts/review_pack.py` and each answers with `SCORE: x/10`, problems, a hook suggestion
and numbered fixes. Process: three rounds per product. After each round the producer applies the fixes that make sense,
rebuilds only the layers that change (directive 17), regenerates the pack and asks again. Scores and what changed are
recorded in `history/<recipe>.md`. The agents never change files themselves.
In Claude Code they run as parallel agents; for n8n `scripts/review_video.py` runs them through an LLM key.
