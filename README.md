# Mecha

**Current launch: [The Edge Kitchen](docs/THE_EDGE_KITCHEN.md), a YouTube cooking channel.** This creator decision supersedes the earlier physics-first and Shorts-first plans.

Healthy, varied recipes that celebrate ingredient flavor, with a warm coastal kitchen and a surf/island atmosphere. Spanish narration comes from the creator; English localization is a later option.

## Start here
- [Channel brief and approved decisions](docs/THE_EDGE_KITCHEN.md)
- [Marble world prompt and reference selection](docs/MARBLE_WORLD_PROMPT.md)
- [Cooking editorial guidelines](docs/SCRIPT_GUIDELINES.md)
- [Assistant-operated workflow](docs/ASSISTANT_WORKFLOW.md)
- [Roadmap](docs/ROADMAP.md) and [actual architecture](docs/ARCHITECTURE.md)
- [Deferred proposals and earlier documentation](Proposals/README.md)

The creator interacts in chat. The assistant prepares scripts, records corrections and operates the local application. No terminal or JSON editing is required from the creator.

## What exists
The Python CLI validates episode data and stores immutable revisions, feedback, approvals and narration in SQLite. It exports portable project bundles and renders landscape storyboard cards or fixed Manim demonstrations with FFmpeg. See the [operator guide](docs/ASSISTANT_WORKFLOW.md) for installation and commands.

**Cooking footage, reusable 3D scenes, Marble imports, AI video generation and YouTube publishing are not implemented.** The orbit example and Manim templates remain developer fixtures, not the channel's creative direction. MongoDB is not part of the current implementation.

## Next deliverable
Validate one consistent kitchen reference set, try a navigable world, and review a short cooking motion proof before commissioning a full recipe video. The first recipe, avatar, duration and publishing cadence remain to be selected. The approved total pilot budget is **€50**, not a separate allowance for every tool.

All previous channel research is retained in `Proposals/`; it does not determine current production priorities. Application code, tests and existing examples are retained.

Code and project documentation are English. Audience content starts in Spanish from Spain. Rendering, script approval and a stored world never constitute permission to publish.
