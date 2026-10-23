# Script, Storytelling and YouTube Guardrails


> **Strategy update (2026-10-17): Shorts-first, two channel tracks.** The creator replaced the immediate long-form launch strategy with two Shorts workflows inspired by the [two-tutorial audit](SHORTS_STRATEGY_AUDIT.md). Preserve Tiene su Física as the proposed micro-explainer track; confirm the second channel's subject before launch. Existing own-voice, originality and no-equation defaults remain. Earlier long-form durations and single-track milestones below are historical/deferred where inconsistent. This is a planning update: the current Python renderer is still landscape and needs a separate vertical implementation.

Applies to every Mecha script, revision, storyboard, narration plan, title, thumbnail and release package.
Owner: creator/editor. Policy sources last checked: **2026-10-17**. Technical documentation is English; initial audience content is Spanish from Spain.

## 1. Mandatory entry point for every script request
Before drafting or changing audience-facing material, the assistant MUST:
1. Read the repository's current `AGENTS.md`, this file and `docs/ASSISTANT_WORKFLOW.md`. Use the active implementation branch while its PR is under review, then the default branch after merge. Resolve the ref to a commit SHA; do not rely solely on chat memory or an earlier copy.
2. Read the current episode revision, creator feedback and approvals. Preserve creator corrections with the revision lease; never rewrite history.
3. Confirm the first channel remains Physics & Engineering unless the creator changes it. Apply the audience/tone below without asking the same preference questions each time.
4. Consult relevant official YouTube sources below when deciding policy questions. Recheck live sources before each upload/publication and whenever an episode introduces a new risk, the stored policy review is over 30 days old, or a policy update is known. The 30-day interval is Mecha's maintenance choice, not YouTube's rule.
5. Record repo commit, guide path, script revision and policy check date in the revision note or companion editorial review. State unresolved issues honestly.

This file defines an assistant/editor review process. The current CLI enforces JSON structure and revision state; it does NOT automatically judge truth, copyright, YouTube compliance, originality or earnings. No script is “YouTube certified” by passing a local test.

## 2. Audience, language and voice — creator requirements
- Platform first: YouTube Shorts. Shorts-first instructions in SHORTS_STRATEGY_AUDIT.md supersede earlier long-form pacing/length defaults. Audience: curious people interested in science, assuming NO prior physics or mathematics knowledge.
- Storytelling and visual intuition come first. Do not include equations, derivations, symbolic notation or dense mathematical graphs by default. Teach mechanisms through everyday situations, analogies, simple animations and clearly explained quantities. Only add an equation when the creator explicitly asks for it or specifically approves a proposed exception; it must not be necessary to follow the story. Internal calculations remain necessary for scientific accuracy even when omitted from narration and visuals.
- Use es-ES with accessible vocabulary understood across the Spanish-speaking audience. Keep code and documentation English.
- Mix conversational phrasing with precise technical terms. Introduce a term in ordinary language before relying on it; explain acronyms on first use.
- Sound like a knowledgeable person explaining an interesting mechanism to a friend. Use short and varied sentences, concrete examples and occasional light humor. Avoid dense lectures, forced slang, patronizing language and unnecessary profanity.
- Ask meaningful questions and build curiosity from the beginning. Deliver useful understanding early; avoid a long greeting, unrelated channel introduction or empty suspense.
- Initial narrator is the creator's recorded voice. Do not replace it with a synthetic voice, clone a third party or imply an expert endorsed the episode.
- Read the script aloud for breath, rhythm and natural Spanish. Start around 125–155 spoken words/minute as an adjustable drafting estimate; use the creator's real recording to set timing.
- Keep narration clear over music; pause for diagrams and unfamiliar quantities. Mark emphasis, pronunciation and intended pauses in the review packet, outside spoken text.
- There is no official YouTube requirement for this accent, word rate, formal/informal ratio or narrator gender. These are Mecha editorial choices, not monetization rules.
- Disclose what platform rules require. Do not reveal personal, confidential employer/client information, private recordings or credentials without authorization. Publicly sourced explanations do not authorize internal company disclosures.

## 3. Original storytelling — editorial defaults, not a formula to mass-produce
Build each episode around one genuine question and one intended takeaway.
Suggested progression, adapted to the topic:
- Opening: an everyday observation, concrete puzzle or surprising verified comparison. Signal the subject and payoff within roughly 20 seconds.
- Early answer: give the viewer a foothold, then show why it works.
- Mechanism: two or three teaching blocks with a specific example or diagram. Each block answers a question and naturally raises the next.
- Application: connect the mechanism to a satellite, aircraft, communications link or everyday engineering system.
- Boundaries: state the model assumptions, scale limitations and a common misconception.
- Ending: resolve the opening, recap the mental picture and invite one relevant next-topic suggestion.

Vary the actual narrative, demonstration and visual plan. Shared branding and reusable rendering code support production; the substance of successive videos must remain distinct. Do not copy another channel's wording, sequence of distinctive scenes or thumbnail composition. Reference audits inspire general craft, not disguised reproductions.
A 6–8 minute pilot remains a useful starting scope, not a mandatory final duration. Prefer the time needed to teach the idea well over padding.

Example tone:
- Prefer: “La gravedad sigue ahí. Lo curioso es que el satélite avanza mientras cae. Vamos a dibujarlo.”
- Avoid: “Este secreto que nadie quiere que sepas cambiará para siempre todo lo que sabes.”
These examples are style illustrations, not approved episode narration.

## 4. Scientific accuracy and assets
Map factual claims and numbers to credible sources, preferably primary scientific/engineering sources. Check units, orders of magnitude, dates and whether the evidence actually supports the claim.
Separate established facts, simplified models, estimates, analogies and impossible hypothetical setups. Explain where an analogy stops working. Never invent studies, quotations, expert credentials, results or sources.
For mechanism diagrams, use reviewed code/native graphics and explicit parameters. Label non-scale illustrations. A visually convincing animation is not proof of accurate physics.
Review visual claims independently of narration: vector directions, relative positions, axes, labels and timings must agree with the explanation.
Use original, licensed or otherwise permitted media and music; retain rights and attribution evidence. A citation alone does not give reuse rights. A copyright claim and a reused-content monetization decision are separate matters. See [YT-COPYRIGHT] and [YT-MONETIZATION].
Reference footage, screenshots and transcripts are research material; do not silently republish them as our own assets.

## 5. YouTube requirements — official-policy summary
Read the linked official documents for context and current details. These summaries are not exhaustive.

### [YT-AI] AI disclosure decision
YouTube requires disclosure for realistic synthetic or meaningfully AI-altered depictions, including invented realistic scenes, altered real-place/event footage or false depictions of real people. Production assistance such as drafting a script/title, captions and clearly nonrealistic animation generally does not require that disclosure by itself. Review audio/music separately; generated music can trigger disclosure requirements.
For Mecha, plain orbit diagrams plus the creator's voice differ from photorealistic invented footage over a real city. Assess actual assets; “educational” or “own narration” is not a blanket exemption.
When required, select the relevant AI/altered-content declaration in the current Studio upload flow; use explanatory scene labels where needed. A description disclaimer does not replace the platform setting. YouTube says disclosure alone does not reduce audience or earning eligibility; repeated nondisclosure may bring penalties. Do not conceal AI use to chase revenue.
Source: https://support.google.com/youtube/answer/14328491?hl=en

### [YT-MONETIZATION] Originality and channel eligibility
AI assistance is not itself disqualifying. YouTube assesses original, substantive educational/creative value and may assess the channel as a whole. Generic, repetitive, interchangeable or mass-produced episodes and minimally transformed third-party material risk ineligibility. Having permission or no copyright claim does not alone satisfy reused-content rules.
Mecha must supply the creator's own reasoning, original demonstrations and meaningful episode differences; cosmetic prompt swaps or a human voice over copied text are insufficient. Current policy also restricts AI-generated personas presenting themselves as human experts on sensitive advice topics; do not invent such authority for future news/politics/health/finance content.
Source: https://support.google.com/youtube/answer/1311392?hl=en

### [YT-ADS] Advertiser suitability
Ad rules cover the entire package, including footage, audio, text, title, thumbnail, description and tags. Context matters. Graphic violence, shocking depictions, hate/slurs, harmful acts, explicit material and exploitative treatment of sensitive events can reduce or remove ad eligibility; some content can also violate Community Guidelines.
Mecha's default is clean vocabulary, non-graphic explanatory visuals and accurate, respectful context. This is intentionally stricter than assuming every permitted profanity is desirable. Scientific or documentary purpose is not automatic ad approval.
Do not exploit an ongoing tragedy or add conflict/disaster keywords solely to gain traffic. Educational reporting can be evaluated differently, but sensitive-event restrictions may apply without gore. Do not evade rules through euphemisms or hidden imagery.
Sources: https://support.google.com/youtube/answer/6162278?hl=en
https://support.google.com/youtube/answer/9269751?hl=en

### [YT-COMMUNITY] Upload eligibility
Community Guidelines apply to public, unlisted and private uploads. Educational/documentary/scientific context is not an unrestricted exception. Review misinformation, deception, dangerous acts and other relevant policies for each specific episode.
Source: https://support.google.com/youtube/answer/9288567?hl=en

### Distinguish outcomes
| Review | What it establishes |
|---|---|
| Community Guidelines | Whether content is allowed; violations may cause removal/penalties |
| Advertiser suitability | Whether an otherwise allowed video can carry full, limited or no ads |
| Channel monetization/YPP | Channel-level eligibility, including originality and other requirements |
| Copyright/rights | Whether assets are permitted; claims can affect availability or revenue |
| AI disclosure | Required transparency for qualifying assets; not an exemption from the other rules |

No assistant can guarantee acceptance, monetization or immunity from enforcement. Correct identified problems before release, use honest self-certification when applicable and request available human review when a decision appears incorrect. Never label an unresolved review “passed.”

## 6. Growth and profitability — separate official guidance from hypotheses
### Official guidance
- [YT-PACKAGING] Use accurate, concise titles and readable, uncluttered thumbnails that represent the actual video. Evaluate packaging using audience-specific analytics, with sufficient impressions, rather than clicks alone.
  https://support.google.com/youtube/answer/12340300?hl=en
- [YT-REVENUE] RPM concerns creator revenue per 1,000 views; CPM concerns advertiser spending and is not interchangeable with earnings. Geography, seasonality and ad availability affect results. Monetization features have separate eligibility requirements.
  https://support.google.com/youtube/answer/9314357?hl=en
- [YT-MIDROLL] Monetized videos at least eight minutes long can enable mid-roll opportunities. Prefer natural transitions; an available slot does not guarantee an ad. Do not lengthen an episode with filler or imply an eight-minute minimum for monetization generally.
  https://support.google.com/youtube/answer/6175006?hl=en

### Mecha commercial hypotheses — not YouTube endorsements
The sources reviewed do not publish a guaranteed “most profitable topics” ranking or a wording/voice recipe for high RPM. Do not invent one or promise income from a reference channel.
Prioritize the overlap of creator expertise, demonstrated audience interest, clear learning value, repeatability, asset rights, production cost and advertiser suitability. Validate demand with actual research when selecting episodes; use measured channel analytics once available.
Candidate areas to TEST, not ranked earnings forecasts:
| Area | Example question | Reason to test |
|---|---|---|
| Satellites/communications | How does internet reach an airplane? | Creator expertise and tangible technology use |
| Space/orbits | Why does a satellite stay above the same place? | Strong diagram-based explanation |
| Electricity/energy | How does electricity reach your home? | Familiar question with broad utility |
| Fluids/aviation | How does a pump move water upstairs? | Everyday physical mechanism |

For the initial channel, prefer evergreen engineering teaching over sensational catastrophe, graphic war coverage or controversy. This is an editorial/commercial risk choice, not proof of higher RPM or a ban on serious topics.
Once eligible, evaluate revenue together with production spend, creator time, viewer satisfaction and repeatability. Compare similar-age releases and meaningful samples. Do not buy fake engagement, mislead sponsors or manipulate platform controls.

## 7. Required editorial review attached to each draft
Keep a compact companion Markdown review with:
- Episode ID/revision; repository commit and guide version consulted.
- Audience, learning goal, hook, early answer, original angle and intended duration.
- Claim/source and unit checks; unresolved factual uncertainties.
- Narrator, visual types and rights/attribution status.
- AI disclosure decision: required / not required / unresolved, rationale by asset type, official source and check date.
- Community Guidelines, advertiser suitability, originality and packaging review, each with rationale; avoid fabricated automated scores.
- Topic/growth hypothesis explicitly separated from official requirements and earnings evidence.
- Creator corrections, approval state and next action.

The current episode JSON schema is strict: do not add invented policy fields. Store this companion review alongside the exported episode bundle using persistent file storage; v0.1 bundles do not automatically include arbitrary sidecar files. Record its reference in the handoff. Review the final rendered assets again before upload because the disclosure decision can change after the script stage.
If a required decision is unresolved, flag it and resolve before public release. Do useful drafting and corrections without inventing clearances.

## 8. Maintenance
This guide supersedes inconsistent earlier tone/policy assumptions in discovery notes. The creator can change editorial preferences; current platform requirements still govern platform use.
Update this document when verified official rules change, preserving source links and review dates. Use primary YouTube/Google documentation for policy claims, not influencer advice or another channel's apparent success.

## Shorts-specific editorial defaults
Use a clear first-second visual/question, one learning payoff, compact narration and mobile-readable captions. For micro-explainers test roughly 25–40 seconds; for original ranking/commentary test 35–60 seconds. These are editorial hypotheses, not platform requirements. Avoid long greetings, filler and copying a competitor's script. Rankings require explicit comparison criteria, substantive original explanation and cleared assets. Do not mechanically apply the long-form eight-minute/mid-roll guidance above to Shorts. Do not adopt tutorial advice to conceal AI, download unlicensed social clips, manufacture engagement or guarantee earnings. Use the official Shorts monetization/classification sources linked in the strategy audit.
