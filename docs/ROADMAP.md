# Implementation Roadmap

The roadmap validates the **two content loops before agent complexity**. Each phase ends in a demonstrable vertical slice.

## Phase 0 — Foundation
Agree product vision, the Natural Worlds and City Walks brands, architecture, domain vocabulary, lifecycle, localization, responsible-synthetic-media policy and roadmap. **Exit:** foundation PR accepted.

## Phase 1 — Content Workspace
Build the application/API skeleton, persistence/migrations, brand profiles, Idea CRUD, locale/audience metadata, workflow state, minimal operator UI, tests and CI. Configure two isolated brand workspaces and their intended YouTube, Instagram and TikTok accounts. **Demo:** enter an `es-ES` idea for either brand and inspect its lifecycle.

## Phase 2 — Research, Locations & Strategy
Build research and map-provider interfaces, source provenance, claims/evidence, location dossiers, POIs, route plans, opportunity assessment, format recommendations, content briefs and human review.

Run a specific Google Maps Platform feasibility spike covering authorized APIs, attribution, storage/retention, rendering and derivative-use constraints. Record an ADR and identify an alternative provider or licensed-footage path before committing to Google imagery.

**Demo:** (a) landscape idea → sourced location/ecology dossier; (b) city + conditions → sourced route and narrative stops.

## Phase 3 — Model Gateway
Create capability-oriented model ports and structured output contracts. Implement hosted adapters for OpenAI GPT and Anthropic Claude plus an OpenAI-compatible adapter for a local vLLM endpoint. Add routing policy, health checks, timeouts, retries, fallbacks, token/cost/latency records, prompt versions and small provider-neutral evaluations.

**Demo:** run the same research-to-storyboard task with one hosted model and one local model, compare outputs and preserve lineage.

## Phase 4 — Media Creation
Build canonical content, storyboard/timeline editing, asset/object storage, revision history, image/video/audio provider ports and asynchronous workers. Add deterministic assembly with FFmpeg, subtitles, narration, upscaling/encoding and review gates.

Deliver two thin vertical slices:
- **Natural Worlds:** one short photorealistic simulated drone journey over a real landscape, optionally with realistic wildlife.
- **City Walks:** one short route-based city walk using only permitted/licensed visual inputs, enriched with sourced contextual narration.

**Demo:** approved brief → reviewed master video with provenance, rights/attribution and AI-disclosure metadata.

## Phase 5 — Platform Derivatives & Publishing
Build the channel contract, OAuth/secrets, brand-to-account mapping, publication state, preview/approval, idempotency/retries and external IDs. Produce 9:16 short-form and 16:9 YouTube derivatives as appropriate, plus captions, titles, descriptions, hashtags, subtitles and thumbnails.

Implement adapters in this order, subject to API access: YouTube, Instagram, then TikTok. Never make browser automation the default publishing mechanism.

**Demo:** one approved master → platform-valid release packages → publish to a test/draft destination → durable external records.

## Phase 6 — Analytics & Experimentation
Build analytics ingestion, normalized cross-platform metrics, collection jobs, brand dashboards, experiments and learning summaries. Keep Natural Worlds and City Walks performance separate while permitting portfolio-level comparison. **Demo:** publication → metrics → experiment result → next-content recommendation.

## Phase 7 — Monetization
Add revenue events, affiliate attribution, sponsor/opportunity records, CTA tracking, revenue by brand/content/channel and opportunity suggestions. **Demo:** trace revenue back to publication → derivative → master → idea.

## Phase 8 — Agentic Automation
Automate validated workflows using durable orchestration, permissions, human checkpoints, retries/timeouts, tracing, budgets, evaluations and recovery. Candidate roles: Research, Location Planner, Storyboarder, Editor, Publisher and Analyst.

**Rule:** agents automate workflows that already work; they do not compensate for an undefined product or bypass rights and policy gates.

## Phase 9 — Scale & Localization
Add locales/markets, further brands and channels, team roles, production hardening, queues/workers, justified service extraction, richer recommendations and additional local/hosted model backends.

## Cross-cutting work
Quality/evaluation, observability, security, responsible synthetic media, rights/attribution, provider-term reviews, cost control and developer experience evolve throughout all phases.

## Decision gate after every phase
1. Did this reduce meaningful creator effort?
2. Did quality remain acceptable or improve?
3. Are the inputs, transformations, rights and disclosures traceable?
4. What did outcomes teach us?
5. Which assumption was validated or falsified?
6. Is the next automation worth its complexity?

## Proposed PR sequence after foundation approval
1. Bootstrap application + engineering baseline
2. Brand, idea and lifecycle model
3. Minimal operator workspace
4. Research/location provider ports + provenance
5. Google Maps feasibility spike + ADR
6. Location dossier, route plan and content brief
7. Model gateway + GPT/Claude adapter
8. vLLM-compatible local adapter + comparison evaluation
9. Asset store + asynchronous media job
10. Natural Worlds vertical slice
11. City Walks vertical slice
12. Platform derivative renderer
13. YouTube publishing adapter
14. Instagram and TikTok adapters
15. Analytics ingestion + first closed-loop experiment

This sequence is deliberately reviewable and can change after the Phase 0 review.
