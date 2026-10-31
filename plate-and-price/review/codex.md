# Codex reviewers

Open Codex with `plate-and-price/` as the working directory. Seven project-scoped custom agents live in `.codex/agents/`, matching `.claude/agents/` by name:

| Agent | Language mode |
|---|---|
| `audience-sociologist` | Separate per language |
| `engagement-analyst` | Shared cut |
| `marketing-strategist` | Separate per language |
| `video-craft-editor` | Shared cut |
| `audio-voice-reviewer` | Shared for music-only shorts; separate with narration |
| `recipe-price-checker` | Separate per language |
| `discoverability-strategist` | Separate per language |

The TOML definitions preserve each Claude role's full review instructions and exact response format. They inherit the parent session's model and reasoning settings rather than mapping a Claude model name to an assumed OpenAI equivalent. They add explicit evidence and read-only limits. The producer remains responsible for edits and render commands.

Codex custom-agent format follows the [official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents). If custom agent discovery is unavailable in the current client, have separate subagents read the corresponding TOML `developer_instructions` and follow those instructions. State that fallback in the review history; do not describe it as native role discovery.

## Run a review

Ask Codex, for example:

> Review only `udon-teriyaki-secreto-iberico-gambones`, format `short`, in English and Spanish. Run the pre-production check first (video-craft-editor, engagement-analyst, recipe-price-checker, marketing-strategist) on the plan, then the post-production check (audio-voice-reviewer, discoverability-strategist, audience-sociologist) on the render. Give every reviewer the recipe/format/language, the checkpoint and the evidence paths. Apply or decline every fix with a reason in one pass and rebuild only changed cached layers; after the post-production check fix only blocking problems and do not start another round. Preserve the dish-name titles and the long video. Do not send email or publish.

From this directory, prepare evidence for each requested language using the existing tools:

```powershell
uv run --with pillow --with imageio-ffmpeg --with edge-tts python scripts/review_pack.py udon-teriyaki-secreto-iberico-gambones --format short --lang en
uv run --with pillow --with imageio-ffmpeg --with edge-tts python scripts/review_pack.py udon-teriyaki-secreto-iberico-gambones --format short --lang es
```

The pack reads the existing render under `PLATE_OUTPUT_DIR/<recipe>/final/`; it does not build a missing video. Verify that the facts, contact sheets, thumbnail and measured audio correspond to the current render before sending them to reviewers. Include source sheets or a source contact sheet when shot choices need review. Record evidence paths and limitations with each check in `review/history/<recipe>.md`.

After each check, the producer reconciles fixes using the owner's rules first, agreement across reviewers second, then severity. Edit the appropriate input or renderer and rebuild affected layers with `scripts/run_pipeline.py <recipe> --format short --lang <language>`. Keep all numbered fixes in the decision log, including declined or deferred items and the reason. There is no second review round; do not manufacture higher scores.

This session-based review does not need an LLM API key. The existing `scripts/review_video.py` is a separate optional API-backed n8n path; creating these custom agents does not change that script's provider or automatically invoke it. Follow the project's credit checks before any paid API use. No review command here sends email or publishes the result.
