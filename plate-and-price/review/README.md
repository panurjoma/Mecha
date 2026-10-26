# Reviewer agents

Before a short or video is called final, three critics judge it from evidence (contact sheet, caption timeline, measured
facts) made by `scripts/review_pack.py`. Each role file in `roles/` is the full instruction for one reviewer. They run as
parallel agents (in Claude Code: one Agent call per role, with the role file as the prompt and the paths of the review
pack; in n8n: `scripts/review_video.py`, which needs an LLM key in `.env`). Each returns a score out of 10, what a real
viewer would do (keep watching, swipe, skip), and numbered, concrete fixes (add, remove, reorder, shorten, retime).
The producer applies the fixes that make sense, rebuilds only the layers that change (directive 17), and runs the
critics again. Two rounds at most, then the owner decides. The critics never change files themselves.
Standards they judge against live in the role files and should be revisited when platform habits change.
