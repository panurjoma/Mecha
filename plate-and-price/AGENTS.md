# Plate & Price instructions for Codex

Read the full [CLAUDE.md](CLAUDE.md) before working here. It is the shared source of project directives, including staged production, cached layers, moving hooks, clean footage, estimated prices and owner approval before publication. Follow the user's current task scope when deciding which products to modify.

The seven Codex reviewers in `.codex/agents/*.toml` preserve the matching Claude roles, response formats and language split. Read [review/README.md](review/README.md) and [review/codex.md](review/codex.md) before running them. Reviewers provide opinions only; the producer owns edits, rebuilds and the decision log.

Use two checks per requested product: a pre-production check on the plan (video-craft-editor, engagement-analyst, recipe-price-checker, marketing-strategist) and a post-production check on the render (audio-voice-reviewer, discoverability-strategist, audience-sociologist), each role once. Review the requested languages separately where required, record scores and apply or decline every numbered fix with a reason in `review/history/<recipe>.md`. After the post-production check fix only blocking problems; there is no second round.

Every workflow must check phone readability: prefer larger coloured captions in the brand palette (cream with a dark outline), verify both languages at rendered size, and keep text clear of food and platform controls. Follow directive 25 in CLAUDE.md; the udon short uses 78 px bold cream captions with a 6 px outline as a starting point.

Do not send email, publish or push merely because a workflow supports those operations. They require the user's explicit authorization. Do not run optional paid review/image APIs without the credit and cost checks in CLAUDE.md. Never print or commit secrets. Report missing evidence, incomplete rendering and untested behavior plainly.
