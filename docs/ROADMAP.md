# Roadmap — The Edge Kitchen first

Updated 2026-10-23. Earlier channel roadmaps are retained in [Proposals](../Proposals/README.md). This plan does not imply that future capabilities are implemented.

| Stage | Deliverable | State / acceptance |
|---|---|---|
| Existing foundation | Local Python episode workflow, SQLite revisions, review, audio and portable bundles | Implemented; current media output is landscape cards / fixed Manim |
| Kitchen continuity | Reconciled floor plan, compatible image references and versioned asset manifest | Next; creator approves island orientation and clear sofa separation |
| World experiment | Marble trial, spatial review and export assessment | Prompt ready; not generated; Blender remains an optional fallback |
| Motion proof | Short shot with the same kitchen, believable cooking action and stable geometry | Planned; compare providers within the €50 total pilot cap |
| Cooking application slice | Register approved external clips and kitchen versions; validate paths/durations/rights; assemble clips with narration | Not implemented; first new code slice after accepted media proof |
| Recipe pilot | Reviewed recipe, script, storyboard, creator audio and final rendered video | Recipe, format, avatar and duration undecided |
| Channel release | Studio setup, accurate packaging/disclosure and private review before explicit publication | Manual first; no publishing integration |
| Localization and iteration | English audio if available and approved; measure audience response, cost and effort | Later; no fixed cadence or earnings promise |

## First implementation scope
Extend the existing application with an explicit cooking asset manifest and a reviewed external-clip composition path. Keep the existing SQLite revision model. Record the kitchen/world version and each clip's source, rights, duration and approval state. Validate media with FFmpeg/ffprobe, assemble deterministically and retain render receipts.

Determine the exact schema after inspecting one real world export and one accepted motion clip. Do not guess Marble APIs/export contracts or make the application execute arbitrary generated Python. Keep existing fixtures and tests.

Acceptance: a creator-approved recipe scene can be assembled from known approved clips plus recorded narration, exported/restored with documented media references, and reviewed without direct CLI work by the creator. Handle missing/private assets explicitly; never silently replace them.

No new runtime implementation, account connection, paid generation or publication is part of this documentation change.
