# Architecture — current implementation and cooking extension

## Implemented today
The creator communicates in chat; the assistant operates a local Python CLI. Validated episode JSON enters SQLite as immutable revisions. Feedback and approvals refer to a specific revision. Narration is copied by content hash. Fixed card/orbit templates render locally; FFmpeg assembles the current preview/final proof. Portable ZIP bundles preserve project history and optionally narration.

See [Assistant workflow](ASSISTANT_WORKFLOW.md) for commands, module responsibilities and limits. SQLite is the current database; MongoDB, a hosted application and an always-on ChatGPT connector are not implemented.

## Planned cooking flow
| Step | Tool / data boundary | Human checkpoint |
|---|---|---|
| Recipe and narration | ChatGPT/Claude assistance; sourced recipe brief and episode revision | Creator reviews recipe, wording and factual claims |
| Fixed environment | Compatible reference images → Marble trial or Blender correction → versioned world/cameras | Approve coherent kitchen layout |
| Scene production | Approved storyboard + kitchen references → selected video tool or local 3D render | Review hands, food states, utensil continuity and geometry |
| Assembly | Proposed Python media manifest → FFmpeg clips, creator audio and captions | Review the actual output and disclosure needs |
| Release | YouTube Studio manually initially | Explicit approval of the exact final release |

Only the existing episode/review workflow and its fixed renderers are implemented. The cooking asset registry, external video provider adapter and clip compositor are future work. Marble exports must be examined before promising format compatibility or camera controls.

## Storage boundaries
- GitHub: code, documentation, example fixtures and versioned configuration.
- Local SQLite / portable episode bundles: revision history, feedback, approval records and asset references.
- Durable media storage: large generated images/world exports/clips and private recordings, with stable references and hashes.
- Proposed asset manifest: source, file hash, kitchen/world version, camera/shot, rights, approval and duration where applicable. This is a design requirement, not a field supported by today's episode schema.

Do not commit media binaries, databases, credentials or private audio to Git. Current bundles do not package arbitrary 3D assets or policy-review sidecars. Do not imply an exported project contains assets it only references.

## Deferred architecture
Previous multi-channel and speculative infrastructure plans are preserved in [Proposals](../Proposals/README.md). Add services and providers only when justified by an accepted pilot.
