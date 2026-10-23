# Working with Mecha through conversation

**Active launch: The Edge Kitchen.** Earlier physics and Shorts plans are deferred to [Proposals](../Proposals/README.md). The orbit commands below remain developer examples; the current renderer does not produce cooking footage.

## Before every script or correction
Read [Script, Storytelling and YouTube Guardrails](SCRIPT_GUIDELINES.md) from the current repo ref and record its commit SHA. Read the [The Edge Kitchen brief](THE_EDGE_KITCHEN.md) as well. These define the cooking audience, recipe checks, source review, originality, disclosure decisions and advertiser-suitability review. Apply it to all drafts and related packaging. This is mandatory for the assistant, not terminal work for the creator.

Keep the required companion editorial review alongside the persistent episode bundle; v0.1 exports only project history and optional audio, not arbitrary sidecar files. Recheck official YouTube policies and actual rendered assets before release; script approval alone is not a policy clearance.

## What the creator does
1. Say: “Create an episode about [topic], for [audience], around [duration].” Topic alone is enough to begin; the assistant proposes missing details.
2. Review the proposed angle, source-backed script and storyboard here in chat.
3. Give natural corrections such as “Explain that more simply” or “Replace the second example.”
4. Record the approved narration and attach the recording.
5. Review a preview, request edits and approve the final release separately.

The creator does not need to edit JSON, use GitHub for each episode or learn the terminal. The assistant uses the application on the creator’s behalf when a runtime and project bundle are available. This is an operator workflow, not an always-on ChatGPT connector; v0.1 does not install an MCP server or run itself inside GitHub.

## What v0.1 implements
- Standard-library Python CLI; validated episode JSON with a sourced claim list and timed scenes.
- SQLite persistence: immutable revisions, corrections, revision-specific approvals and render receipts.
- Content-addressed copy of the creator’s local narration; integrity checks on reuse.
- Fixed Manim card/orbit templates; FFmpeg assembly; scene-level SRT and Markdown review packets.
- A separately labeled FFmpeg card storyboard when Manim is unavailable. It does not pretend to show an orbital animation.
- Scene cache, final-output checksums and cache invalidation when script, audio or templates change.
- Portable ZIP export/restore with the full revision/feedback history, optionally including narration.
- Machine-readable JSON command results and actionable errors. No cloud accounts or API keys required.

## Install and check
Python 3.11+ is required. On Ubuntu, FFmpeg and fonts are system packages:

```sh
sudo apt-get update
sudo apt-get install -y ffmpeg fonts-dejavu-core
python -m pip install -e .
mecha doctor
```

For actual Manim animation (fixed at 0.19.0 for this first renderer):

```sh
sudo apt-get install -y libcairo2-dev libpango1.0-dev pkg-config
python -m pip install -e '.[animation]'
```

Use a virtual environment in a regular developer environment. For Windows/macOS follow [Manim’s installation guide](https://docs.manim.community/en/stable/installation.html) and install FFmpeg/fonts for that OS. No LaTeX dependency is required by these templates. Native dependencies can be unavailable in a hosted session; the assistant must report that instead of claiming animation was tested.

## Assistant command sequence
Use a durable workspace when available. The default `.mecha/` directory is ignored by Git. All commands are local, with no network/model calls.

```sh
mecha --workspace /path/to/workspace ingest examples/orbit-proof.json --note 'Initial illustrative draft, not creator-approved'
mecha --workspace /path/to/workspace status orbit-proof
mecha --workspace /path/to/workspace review orbit-proof /path/to/review-r1.md
mecha --workspace /path/to/workspace feedback orbit-proof --expected-revision 1 --text 'Exact creator correction'
```

The assistant edits a full JSON document using `examples/orbit-proof.json` as the contract example, then imports it as revision 2:

```sh
mecha --workspace /path/to/workspace ingest /path/to/revised.json --expected-revision 1 --note 'Shorten opening in response to creator feedback'
mecha --workspace /path/to/workspace history orbit-proof
mecha --workspace /path/to/workspace render orbit-proof --renderer cards
```

The example is a 60-second draft to exercise the pipeline; its timing, public brand and topic are not a creator decision. A silent render before narration is legitimate but is only a visual/storyboard preview. `--renderer manim` animates the orbit diagram. The template is idealized and not a simulation or to-scale display.

Record approvals ONLY after the creator grants them; the following are command templates, not approvals:

```sh
mecha --workspace /path/to/workspace approve orbit-proof --expected-revision 2 --stage script --note 'Exact creator instruction'
mecha --workspace /path/to/workspace approve orbit-proof --expected-revision 2 --stage storyboard --note 'Exact creator instruction'
mecha --workspace /path/to/workspace attach-audio orbit-proof /path/to/creator-recording.wav
mecha --workspace /path/to/workspace render orbit-proof --renderer manim --final
```

The full recording must match total scene duration within 0.5 seconds. The assistant adjusts durations after inspecting the recording; v0.1 does not perform speech recognition or forced alignment. Subtitles are scene-level, not word-aligned. Final proof requires current approvals and audio; it is not authorization to publish. Audio and script correspondence, factual accuracy, pronunciation, loudness and readability still require human review.

## Persistence and handoff
The SQLite workspace is the current local source of truth. A review packet or chat history alone is not enough to restore editable state.

```sh
mecha --workspace /path/to/workspace export orbit-proof /path/to/orbit-proof-r2.zip
# Add --include-audio only when storing that private recording is authorized.
mecha --workspace /path/to/new-workspace restore /path/to/orbit-proof-r2.zip
```

Export after corrections/approvals and save the ZIP using the assistant’s persistent file-storage tools. The application creates the bundle; it does not upload to ChatGPT Library itself. Save the original narration separately or include it explicitly. Generated MP4s can be saved separately and recreated; bundles contain input/history, not render caches.

At the end of a session provide episode ID, revision, pending decisions, saved bundle/file reference and next action. In a new session retrieve the most recent bundle, restore into a fresh workspace, inspect `status`/`history` and continue. Do not rely on hidden memory or assume a workspace survives inactivity. Restore never overwrites an existing episode; compare in a new workspace.

Bundles are ZIPs with `project.json` and optionally `audio/<sha256>`. Restore validates revisions, hashes, known archive members and size limits; it never extracts arbitrary paths. This is not a signed identity or permission format: approvals are local audit entries and require creator verification before consequential external actions.

## Code organization and execution flow
| Module | Responsibility |
|---|---|
| `models.py` | Strict episode/scene/claim validation and canonical hashes |
| `store.py` | SQLite state, revision leases, audio assets and portable bundles |
| `review.py` | Human-readable script/storyboard/correction packet |
| `render.py` | Fixed-template rendering, caching, subprocess timeouts and FFmpeg muxing |
| `manim_scene.py` | Reviewed card and orbit animation templates |
| `cli.py` | Assistant/operator interface |

Chat instructions → assistant edits structured episode → Python validates/persists → Manim renders clips → FFmpeg assembles with recording → assistant presents review → export durable handoff.

## Limits and next slices
No automatic ChatGPT/Claude API integration, paid generation, arbitrary generated code, Blender adapter, transcription, web UI, MCP server or YouTube upload. Existing assistant access can draft scripts, and the assistant imports them; connecting to YouTube is separate future OAuth work. Do not claim these are already connected.

The core workflow has no third-party Python dependencies. FFmpeg rendering needs local codecs/fonts; Manim has optional native dependencies. Resource bounds cover JSON size, scene count/duration, bundle/audio size and subprocess timeouts, but this is a trusted local single-operator application, not a hardened multi-tenant service.

Next: reconcile and approve kitchen references → test the [Marble world prompt](MARBLE_WORLD_PROMPT.md) → review one cooking motion proof → implement an external-clip/asset workflow → choose the first recipe and produce a reviewed pilot. Publishing integration remains separate future work.
