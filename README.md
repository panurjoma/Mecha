<div align="center">

<img src="assets/mecha-flame.svg" alt="Mecha flame" width="150" />

# Mecha

### One idea lights everything.

**An AI-assisted engine for original, researched, reviewable digital content.**

[Vision](docs/VISION.md) · [Architecture](docs/ARCHITECTURE.md) · [Roadmap](docs/ROADMAP.md) · [Physics plan](docs/PHYSICS_CHANNEL_PLAN.md) · [Reference audit](docs/REFERENCE_AUDIT_LAST_TWO.md)

`Spanish (Spain) first` · `English docs & code` · `Human-guided` · `YouTube first`

</div>

## First launch: Physics & Engineering Explained

Make complex systems understandable through simple explanations, accurate diagrams and concrete applications. Begin with the creator’s expertise in satellites and communications, then expand into space, aircraft, fluid mechanics, electricity and energy.

The creator chooses topics one at a time and reviews the angle, script, technical accuracy, visual proof and final release. Proposed first topic: **Why doesn’t a satellite fall to Earth?** Topic and public brand name await selection.

## Planned portfolio

| Channel | Viewer experience | Status |
|---|---|---|
| Physics & Engineering Explained | Intuitive explanations of how physical and engineered systems work | **First implementation** |
| AI Explained | Complex AI concepts and technologies explained simply | Later |
| Relaxing Aerial Journeys | Realistic drone-style journeys for relaxation | Later |
| Current Affairs Explained | Context for world news, conflicts and emerging technology | Later |

Only one YouTube channel launches initially. Later-channel order is undecided. City walks/urbanism are optional future work; company histories are parked. Instagram and TikTok are deferred.

## Production workflow

Topic → sourced brief → script and technical review → timed storyboard → voice/visual proof → render and review → private upload → approved publication → learning.

Recommended starting stack: **Python, Manim Community and FFmpeg**, ChatGPT/Claude assistance and the creator’s recorded narration. Blender is available for specific 3D needs; cinematic generation is optional. See the [costs and creator input checklist](docs/PHYSICS_CHANNEL_PLAN.md).

## Roadmap

| Stage | Demonstrable outcome |
|---|---|
| Foundation | Agree physics-channel format, voice, first topic and spend |
| Short proof | A reviewed 60–90 second sequence |
| Full pilot | One reviewed 6–8 minute episode and release package |
| YouTube | Private upload, creator approval and reliable publication |
| Repeatability | Three episodes with measured production cost and effort |
| Expansion | Add only capabilities justified by results |

## Architecture

Start as a modular monolith with provider ports and durable episode state. Keep scripts, source claims, diagram parameters, asset lineage, costs and approvals linked. Cache approved assets and rerender only affected scenes.

Reference analysis informs original storytelling; it does not establish which AI tools another creator uses. Precise mechanisms are rendered from reviewed parameters, and synthetic illustrations are identified appropriately.

## Repository status

**First local implementation — assistant-operated episode workspace.**

[PR #2](../../pull/2) merged the foundation. The first application now imports episode scripts/storyboards, preserves revisions and corrections in SQLite, imports your recording, renders previews and exports portable project bundles. The assistant operates it; the creator can stay in conversation. See the [conversation workflow and handoff guide](docs/ASSISTANT_WORKFLOW.md).

```sh
python -m pip install -e .
mecha doctor
mecha ingest examples/orbit-proof.json --note 'Illustrative draft, not creator-approved'
mecha review orbit-proof review-r1.md
mecha render orbit-proof --renderer cards
mecha export orbit-proof orbit-proof-r1.zip
```

FFmpeg and fonts are required for the labeled card storyboard. Install `.[animation]` and native dependencies for real Manim animation, then use `--renderer manim`. The sample is a 60-second unapproved proof, initially silent. No paid API calls or public publishing are implemented. Blender is optional future work.

Tests: `python -m unittest discover -s tests -v`. Native animation integration: `MECHA_TEST_MANIM=1 python -m unittest discover -s tests -v` with Manim installed. GitHub Actions runs both the core and native-animation jobs.

[Issue #1](../../issues/1) tracks foundation planning.

