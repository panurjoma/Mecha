# Contributing to Mecha

## Language
- Code, commits, issues, PRs and technical documentation: **English**.
- Generated audience-facing content: initially **Spanish from Spain (`es-ES`)**.
- Do not embed Spanish copy into domain/application logic; use explicit localization/content configuration.

## Working model
1. Start from an issue describing the outcome.
2. Keep PRs conceptually reviewable.
3. Link the issue from the PR.
4. Test behavioral changes.
5. Record long-lived architectural decisions.
6. Prefer vertical slices over speculative infrastructure.

## Architecture discipline
Keep domain logic independent from provider SDKs; do not introduce a service or agent without a concrete requirement; persist long-running workflow state; preserve provenance; keep external side effects observable and retry-safe.
