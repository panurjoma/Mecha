# Implementation Roadmap

The roadmap validates the **content loop before agent complexity**. Each phase ends in a demonstrable vertical slice.

## Phase 0 — Foundation
Agree product vision, architecture, domain vocabulary, lifecycle, localization decision and roadmap. **Exit:** foundation PR accepted.

## Phase 1 — Content Workspace
Build application/API skeleton, persistence/migrations, Idea CRUD, workspace, locale/audience metadata, workflow state, minimal operator UI, tests and CI. **Demo:** enter an `es-ES` idea, persist it and inspect its lifecycle.

## Phase 2 — Research & Strategy
Build research provider interface, source provenance, claims/evidence, research dossier, opportunity assessment, audience/angle/format recommendation, content briefs and human review. **Demo:** idea → sourced dossier → approved brief.

## Phase 3 — Creation Pipeline
Build canonical content, prompt/config versioning, AI provider interface, asset storage, revision/history, editorial review, derivatives and media-provider interfaces as needed. Start with the smallest useful format. **Demo:** approved brief → canonical content → reviewed derivative.

## Phase 4 — Publishing
Build channel adapter contract, credentials/OAuth, publication state, scheduling, preview/approval, idempotency/retries, external IDs and the first one or two real adapters. **Demo:** approved derivative → publication → durable external record.

## Phase 5 — Analytics & Experimentation
Build analytics ingestion, normalized metrics, collection jobs, dashboards, experiments and actionable learning summaries. **Demo:** publication → metrics → experiment result → next-content recommendation.

## Phase 6 — Monetization
Add revenue events, affiliate attribution, sponsor/opportunity records, CTA tracking, revenue by content/channel and opportunity suggestions. **Demo:** trace revenue back to publication → derivative → canonical content → idea.

## Phase 7 — Agentic Automation
Automate validated workflows using durable orchestration, permissions, human checkpoints, retries/timeouts, tracing, budgets, evaluations and recovery. Candidate roles: Research, Strategy, Creator/Editor, Publisher, Analyst.

**Rule:** agents automate workflows that already work; they do not compensate for an undefined product.

## Phase 8 — Scale & Localization
Add locales/markets, channels, brands/workspaces, team roles, production hardening, queues/workers, justified service extraction and richer recommendations.

## Cross-cutting work
Quality/evaluation, observability, security, responsible automation and developer experience evolve throughout all phases.

## Decision gate after every phase
1. Did this reduce meaningful creator effort?
2. Did quality remain acceptable or improve?
3. What did outcomes teach us?
4. Which assumption was validated/falsified?
5. Is the next automation worth its complexity?

## Proposed PR sequence after foundation approval
1. Bootstrap application + engineering baseline
2. Idea/domain model + lifecycle
3. Minimal operator workspace
4. Research provider + provenance
5. Research dossier + content brief
6. Canonical content + review
7. First channel derivative
8. First publishing adapter
9. Analytics ingestion
10. First closed-loop experiment

This sequence is deliberately reviewable and may change after Issue #1.
