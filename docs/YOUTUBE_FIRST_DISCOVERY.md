# YouTube-first channel discovery
Updated: 2026-10-17. Status: working proposal awaiting creator feedback.

## Confirmed scope
Launch ONE Spanish-from-Spain YouTube channel first. Technical documentation and code remain English. Do not create five channels. Natural Worlds and City Walks remain future portfolio options; Instagram and TikTok are deferred.

## Repository baseline
At inspection, private repository panurjoma/Mecha had open, non-draft, mergeable PR #2, head docs/foundation-roadmap at c146016999b602610a4e78dac2f263fe3f7e4472, targeting main at 5012a8952b34848aa24260bcc84d16748e515d71. PR references planning issue #1. Existing work was documentation, architecture and SVG identity, with no production implementation. This records the PRE-UPDATE state, not the current branch SHA.
Finish channel/technology decisions interactively, update this foundation PR, then resolve it before starting implementation. Do not discard its documentation by closing it unmerged accidentally; confirm whether “close out” means merge when finalizing.

## Reference: The Last Day
URL: https://www.youtube.com/@thelastday01
Evidence: two user-supplied screenshots from an advertisement, plus limited public indexing. Channel pages were throttled/unavailable through public retrieval. NO complete upload inventory, transcripts, audiovisual review or verified production stack has been obtained. Do not label this a completed all-video audit.
The screenshot shows 19 videos and 18.1K subscribers at an unknown capture date; these are not current verified statistics.
Two visible examples:
- “Nepal’s 2026 Disaster Explained: The Glacier That Wiped Out a Valley” — screenshot duration 19:19.
- “The Wave That Was Taller Than a Skyscraper” — thumbnail label “LITUYA BAY”, screenshot duration 12:32.
The examples concern place-specific disasters and scale, rather than establishing a channel exclusively about human extinction. Their titles and thumbnails do not establish the historical accuracy of their claims.

### Observable packaging
Large readable place/event labels, one dominant catastrophe image, landscape format, spectacle and scale, curiosity-led titles, documentary-length uploads. The screenshot is a promotional example, not proof of revenue, authorship, tool usage or production cost.

### Proposed storytelling hypothesis — NOT verified from playback
Cold-open consequence/question → locate event in place/time → establish normal life and vulnerability → explain mechanisms with visual escalation → pivotal event → aftermath → lessons and a satisfying answer.
For Mecha, open with a concrete question, earn suspense through causal explanation, use sourced measurements, vary maps/diagrams/reconstructions, and distinguish fact, reconstruction and hypothetical scenario. Avoid unsupported timestamps or claims that this is the reference channel’s observed retention formula.

### Required exhaustive audit
Obtain the channel ID and paginate all public uploads, including Videos, Shorts and livestream archives. Record retrieval date and reconcile inventory; the screenshot count is not the expected current count. For EVERY upload record ID, canonical URL, title, date, duration, accessible metrics, thumbnail, description, transcript availability/language, chapter outline and evidence access.
Inspect opening, scene changes, narration, music, captions, ending, sources, disclosures and repeated visual artifacts with timestamps. Keep metadata-only, transcript-reviewed and audiovisual-reviewed coverage separate. Mark inaccessible entries and do not claim complete review unless all entries have evidence. Compare median-normalized performance; do not treat a viral outlier as a reliable earnings forecast.
vidIQ was found in ChatGPT’s plugin directory and suggested, but was NOT connected at discovery. Its advertised channel/transcript/visual-analysis capabilities may help; actual access and catalogue completeness must be verified. No official first-party YouTube management plugin was established by this search.

## Screenshot tool identification
| Position | Identification | Confidence / role |
|---|---|---|
| Top left, orange pixel creature | Claude Code / Clawd | High visual confidence; scripting/coding/orchestration candidate. Not an image/video engine. |
| Top right, two black bars | ElevenLabs | Confirmed against official brand symbol; narration/audio candidate. |
| Bottom left, black fluid mark on neon yellow-green | Higgsfield | High visual confidence; image/video generation suite candidate. |
| Bottom right, purple-blue cloud/flower with terminal glyph | Unresolved | Do not select or budget an unidentified product. Nexlev is a research candidate, NOT a confirmed match. |
The advertisement’s tool collage does not prove the reference creator uses any of these products.

## Five alternative channel concepts
Working names only; availability/trademark checks pending.
| Concept | Editorial promise | Example pilot | Production / research burden |
|---|---|---|---|
| Punto de Ruptura | Explain real moments when natural systems overwhelmed people | “Lituya Bay: how could a wave reach that high?” | Medium visuals; high fact-checking; closest to reference |
| La Tierra Antes | Visit real landscapes in deep time, with realistic extinct wildlife | “A day in Iberia before humans” | High visual/continuity and palaeontology burden |
| Ciudades que Fueron | Reconstruct a city at a defined historical moment through a narrated journey | “A walk through Roman Mérida” | High architectural/source burden; related to City Walks |
| Mundos Ocultos | Reveal spectacular real environments and the science behind them | “What lies beneath a glacier?” | Medium burden; connects to Natural Worlds; recommended starting candidate |
| Después de Nosotros | Clearly labeled scientific hypotheticals about a world after humans | “What would happen to Madrid without maintenance?” | High extrapolation burden; separate evidence from speculation |

Recommendation is provisional: Mundos Ocultos fits the existing landscape direction and offers a broad supply of visually rich, sourceable episodes. Choose Punto de Ruptura if closeness to the supplied reference matters most. No demand study has yet validated either choice.

## Technology and cost choices
Prices checked from official public pages on 2026-10-17; USD, before applicable taxes. No purchases authorized or made.
| Stage | Low-cash candidate | Paid candidate / known cost | Selection condition |
|---|---|---|---|
| Research/script | Manual source research and available assistant; local model subject to hardware/license evaluation | Claude Pro listed at $20/month; optional | Consumer subscriptions do not establish API entitlement; automated API cost needs a separate estimate |
| Narration | Creator’s own recording | ElevenLabs Starter $6/month, 30k credits; Creator $22/month, 121k credits | Paid commercial license; evaluate es-ES pronunciation and voice rights; exclude introductory discounts from baseline |
| Images/video | Licensed/public-domain media plus original diagrams; self-hosted Wan2.2 candidate | Higgsfield credit-based plans | Model, quality, duration, retries and automation access determine cost; advertised annual equivalents are not monthly commitments |
| Assembly | FFmpeg; evaluate Kdenlive for manual editing | Optional editor later | Deterministic timeline, audio mix, captions, export |
| Research analytics | Manual YouTube research/Studio | vidIQ or Nexlev optional | Do not buy both initially; verify actual tiers and connector access |
| Publishing | Manual YouTube Studio for pilot | YouTube API adapter later | Verify current API requirements, OAuth, quotas and private/scheduled publishing support |

Official ElevenLabs free tier has 10k credits; paid Starter adds commercial licensing. Do not build a commercial voice workflow around an assumed free commercial license. At roughly 8,000 characters per 10-minute script, four scripts consume about 32k credits at one credit/character, BEFORE retries; Starter may be insufficient. This is a planning example, not a fixed narration rate.
Wan2.2 upstream specifies Apache 2.0 and a 5B path requiring at least 24GB GPU memory; open weights do not eliminate hardware, electricity, storage or rental cost. Benchmark actual target resolution/duration before choosing local generation.
Higgsfield’s accessible creation page advertised Basic $9/month BILLED ANNUALLY and Pro $23/month BILLED ANNUALLY against $29 monthly; the pricing route was dynamically rendered and other official marketing pages showed inconsistent tiers. Treat final pricing/API inclusion as unresolved until checkout/account terms are verified. Do not assume unlimited web generations apply to an API.

### Budget envelopes — proposed caps, not vendor quotes
- Minimal cash: $0 incremental subscriptions using own narration and existing resources; excludes existing subscriptions, hardware, electricity and time.
- Balanced pilot: cap $60/month for voice, selective visual generation and optional text API usage; fit tested against actual credits before committing.
- Cinematic experiment: cap $150/month initially; fully generated long-form may exceed this and is not promised.
Start with one 60–90 second proof, then a 6–8 minute pilot; approve a repeatable cost only after measuring both.

Per-video estimate = allocated subscriptions + text usage + generated seconds × effective cost/second × attempts + narration retries + compute/storage/licensed assets.
For a 10-minute video, 20% generated footage = 120 accepted seconds. At hypothetical $0.10/second and 2.5 attempts: $30 of generation. At 100%: $150, before other costs. This is illustrative arithmetic, not a quote or a measured acceptance rate.

## Proposed pilot workflow
Choose topic/channel and budget → source dossier and claim table → original es-ES script → shot list and timed storyboard → narration test → low-resolution visual proof → approve quality/cost → generate only selected shots → deterministic assembly → factual/visual/audio review → private upload → creator approval → publish → inspect early retention and production cost.
Use licensed footage, original maps/diagrams and moving stills for explanatory sections; reserve generated clips for high-value moments. Synthetic reconstructions must not masquerade as genuine disaster footage. Verify current YouTube synthetic-media and monetization requirements during publishing implementation.

## Architecture additions
Retain modular monolith and provider ports. One active BrandProfile/ChannelAccount initially. Add Episode, ClaimEvidence, ScriptRevision, ShotPlan, CostEstimate, GenerationAttempt, RightsRecord and ReleasePackage. Persist model/config/prompt lineage and accepted/rejected attempts. Provide per-run and monthly cost caps, cancellation, caching and resumable rendering.
Select one implementation provider per required capability after feedback; existing GPT/Claude/vLLM options remain extensibility directions, not mandatory simultaneous integrations. The screenshot does not determine provider selection.
Reference research and analytics are distinct from rendering/publishing adapters; a ChatGPT plugin does not automatically become an application integration.
Deferred: extra brands, geographic route machinery unless needed by the selected concept, Instagram, TikTok, cross-platform derivatives, autonomous agents and monetization features.

## Decisions still required
1. First channel concept (choose one).
2. Monthly incremental budget and existing usable hardware/subscriptions.
3. Preferred narration: own voice or synthetic es-ES.
4. Pilot visual target and initial length.
5. Complete reference audit/access, unresolved purple icon, final provider/API pricing.
6. Final review and resolution of PR #2 before implementation.

## Sources
- User screenshots and supplied channel URL (observations limited as described).
- https://elevenlabs.io/brand
- https://elevenlabs.io/pricing
- https://claude.com/pricing
- https://higgsfield.ai/pricing
- https://higgsfield.ai/create/video/select?for=motion&model=seedance1_5
- https://github.com/Wan-Video/Wan2.2
- https://www.nexlev.io/ (research product with free/paid offerings and advertised MCP; not confirmed screenshot identity)
