# Physics and Engineering — first-channel plan
Status: physics-channel priority and technology baseline APPROVED on 2026-10-17. Own voice selected. Public brand name, first topic, style details and any paid budget remain implementation decisions. Documentation language: English. Audience language: Spanish from Spain.

## Approved technology baseline — 2026-10-17

- Python + Manim Community + FFmpeg approved. Manim is a Python animation library for diagrams, vectors, orbits and other explanatory graphics; FFmpeg assembles and encodes video/audio/subtitles.
- Blender approved as optional, used only where 3D improves understanding. These tools have no software subscription fee; hardware, electricity, optional assets/add-ons and cloud rendering are separate.
- Use a mix of ChatGPT/OpenAI and Claude/Anthropic for drafting and critical review. Start with operator-assisted use of existing access. Automatic API adapters are a later implementation step with separately priced usage and explicit credential setup; no API spending or new subscriptions approved.
- Own recorded voice is selected. ElevenLabs is deferred because its free plan is non-commercial and limited; do not assume free commercial narration.
- Keep es-ES as the working launch locale. Recommend Spanish first with broadly understandable technical vocabulary for Spain and Latin America; the creator is still considering language. English localization can reuse reviewed scenes after the format works.
- Connecting the assistants to YouTube is an intended future capability, not a completed connection. The current verified vidIQ connection returned no owned channel. Do not infer ChatGPT/Claude publishing authorization.
- Foundation documentation may now be merged. Topic, public name, cadence, style details and any paid budget are episode/implementation decisions, not blockers for this planning PR.

Spanish positioning: established science channels such as QuantumFracture and Date un Vlog demonstrate an existing audience and competition. A satellite/communications/practical-engineering focus is a proposed differentiator; no quantitative Spanish-versus-English competition, revenue or demand study has been completed.
Sources: https://docs.manim.community/en/stable/ ; https://www.blender.org/about/license/ ; https://ffmpeg.org/about.html ; https://elevenlabs.io/terms-of-use-eu ; https://www.rtve.es/play/videos/fecyt/sciencetruck-2-fisica-youtuber-jose-luis-crespo/5730676/

## Confirmed portfolio
| Priority | Channel concept | Scope | Launch status |
|---|---|---|---|
| 1 | Physics & Engineering Explained | Satellites, space, communications, aircraft, algorithms in engineered systems, fluid mechanics, pipes, electricity and energy | FIRST implementation |
| Later | AI Explained | Simple explanations of complex AI concepts and technologies | Planned; no parallel launch |
| Later | Relaxing Aerial Journeys | Realistic drone-style journeys over natural/built environments | Planned; synthetic footage identified |
| Later | Current Affairs Explained | World news, conflicts and emerging technologies, with context | Planned; no parallel launch |

Launch order among the later three is undecided. Urbanism/city walks remain an optional later direction within or alongside aerial journeys; do not force narrated urbanism into the relaxing format. Company histories are parked. Earlier five-concept suggestions remain historical alternatives, superseded by this portfolio.

## Editorial promise and differentiation
Make difficult physical systems understandable through everyday questions, faithful animated explanations and concrete use cases. Start with the creator’s satellite/communications expertise, then expand into related engineering topics.
Target assumption for review: curious adults without specialist training; intuition first, limited equations when they help. Expertise guides technical review; professional experience is not permission to disclose employer-confidential material.
Working name option: “Así Funciona”. Availability and identity have not been checked.

## Recommended pilot and initial series
Proposed first episode: “Why doesn’t a satellite fall to Earth?”
Core outcome: understand orbit as continuous free fall with sideways velocity. Distinguish orbital motion from hovering. Clearly label idealizations and scale.
Follow-up candidates, chosen one at a time by the creator:
1. How does internet reach an airplane?
2. Why is satellite internet delayed?
3. Why does a satellite seem fixed in the sky?
4. How does an antenna send information through empty space?
Later bridges: lift, pumps/pipe pressure, electricity generation, heat transfer and control/communications algorithms.
No episode is selected automatically; creator supplies or chooses the next topic.

## Technology recommendation
| Capability | Start with | Cost / qualification |
|---|---|---|
| Workflow/contracts | Python CLI, Pydantic-style structured validation, SQLite manifest, local asset folders | No software subscription; exact dependency versions selected at implementation |
| Research and script | One text-model adapter, initially operator-assisted; select hosted API or local endpoint after quality/cost comparison | Existing chat subscriptions are not API credit; no API model/provider purchased or fixed yet |
| Explanatory 2D animation | Manim Community + original SVG assets | Open source, MIT; suitable for reproducible vectors, paths, charts and simple geometry |
| Selective 3D | Blender scripted with Python when an episode needs it | Free/open source; rendering time and asset rights still matter; defer until 2D proof shows a need |
| Narration | Compare creator recording against licensed es-ES synthetic voice | Own recording has no provider fee; ElevenLabs Starter $6/month / Creator $22/month regular baseline, pre-tax |
| Assembly | FFmpeg + ffprobe | Free software; deterministic timeline, audio mix, subtitles and export |
| Research analytics | Connected vidIQ, selectively | Credit-metered; current two-video audit uses 80 credits; separate from generation budget |
| Publishing | Manual private YouTube Studio upload for pilot | API adapter after workflow validation; public release requires creator approval |
| Cinematic shots | Optional Higgsfield or another provider after testing | Deferred; no subscription needed to demonstrate orbital mechanics |

Recommendation: Python + Manim + FFmpeg, one text adapter and one narration choice. Use Blender for specific 3D needs. Generative video can illustrate atmosphere, but exact orbital paths, wave behavior, charts and mechanisms should come from code/native graphics with reviewed parameters.
A convincing animation is not automatically a physically accurate simulation. Units, equations, reference frames, scale and model assumptions must be checked.
Do not build the first channel around four simultaneously mandatory subscriptions, a complex agent system or cloud GPU infrastructure.

## Cost model
Starting target: own narration + deterministic diagrams can avoid new voice/video subscriptions; compute, existing subscriptions, text API usage and creator time remain costs.
If using ElevenLabs, baseline recurring voice option starts at $6/month, but 30k credits may not cover four 6–8 minute episodes plus revisions. At 150 words/minute and roughly six characters/word, 8 minutes is about 7,200 characters; four episodes are 28,800 before retries. Actual script length/model credit rate determines fit. Creator at $22/month offers more headroom.
Proposed software/service envelope: $10–30/month for low-volume voice and text usage, excluding taxes, current subscriptions and hardware; this is an unapproved planning target, not a quote, minimum or purchase authorization.
Do not promise automated API production at $0 without measuring quality and compute. Do not buy annual plans at pilot stage.
Record cost per accepted minute, generation attempts, editing time and revision count.

## Human-guided generation workflow
1. Creator submits topic + intended takeaway.
2. Mecha proposes audience framing, 2–3 angles, outline, sources and provisional cost.
3. Creator approves angle and technical depth.
4. Draft original es-ES script and a claim/source/unit checklist. Creator reviews technical correctness and voice.
5. Generate a timed storyboard with exact diagrams, labels, scale caveats and optional illustration shots.
6. Produce a 60–90 second low-resolution proof and a short voice sample. Creator reviews visual clarity, pacing and pronunciation.
7. Render the approved full 6–8 minute pilot; assemble soundtrack, captions, chapters, thumbnail and description.
8. Review master and release package; private upload; creator approves public release.
9. Record actual effort/cost and available audience metrics before automating further.

Future automation should stop at explicit review checkpoints with persisted revision state. Feedback on one scene regenerates that scene only; approved narration and assets should be cached.
Initial finite pipeline is sufficient; agents can be considered after repeatable production works.

## Episode input template
Required: topic, what the viewer should understand, and any technical point the creator wants emphasized.
Optional: target audience, length, source links, analogy ideas, what to omit, visual preferences, voice, maximum spend and deadline.
Defaults proposed for feedback: es-ES, curious non-specialists, 6–8 minutes, calm conversational narration, clean labeled diagrams, restrained cinematic opening, one teaching goal.

## Feedback requested before implementation
- First topic: proposed orbit episode or a creator-supplied alternative.
- Audience/depth: general curiosity, secondary-school level or technically curious adults.
- Visual style: mostly clean diagrams, mostly cinematic, or hybrid (recommended).
- Narration is selected: creator recording. Review recording quality and pronunciation using a short sample.
- Monthly/new-service budget and approximate episode frequency.
- Available computer/OS and optional GPU for rendering/local models.
- Any reference channels, branding preferences or prohibited analogies.

Channel priority is already decided; do not repeatedly ask which of the four to launch.

## Architecture and acceptance
Keep the existing modular-monolith/provider-port direction. First vertical slice is a CLI-driven episode project, not a multi-brand dashboard.
Contracts: EpisodeBrief, ClaimEvidence, ScriptRevision, SceneSpec, NarrationAsset, RenderManifest, CostLedger, ReviewDecision and ReleasePackage.
Scene specs carry start/duration, source/claim links, diagram parameters with units, narration span, renderer and assets. Persist approval revision hashes; downstream changes invalidate affected approvals.
Render generated code in constrained jobs with bounded resources; validate external inputs and keep secrets out of manifests. Secrets are configured only when implementing an approved provider.
Verification: review numerical examples, units and diagram geometry; check media duration/sync, text readability, subtitle timing, audio clipping/loudness and successful render. Test substantive workflow behaviors such as resumability, stale approval and duplicate publishing when implemented.

## Later-channel distinctions
AI: mechanism/intuition with dated model claims, reproducible demonstrations and no unsupported benchmark conclusions.
Relaxing aerial journeys: long smooth shots, restrained sound and explicit synthetic status; factual geography and wildlife validation. Urbanism narration, if pursued, needs a distinct editorial format.
News: separate verified events from interpretation; record event/publish/update dates, multiple credible sources, disputed claims and correction history. Synthetic depictions must never look like authentic breaking-news evidence. High freshness makes this a later workflow.
These are roadmap requirements, not an instruction to scrape news or launch extra channels now.

## Sources
- https://docs.manim.community/en/stable/
- https://www.blender.org/about/license/
- https://ffmpeg.org/about.html
- https://elevenlabs.io/pricing
- [Reference audit](REFERENCE_AUDIT_LAST_TWO.md)
