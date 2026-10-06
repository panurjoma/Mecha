# Product Vision

## Mission
Mecha helps a creator turn a promising idea into original, evidence-backed content and continuously learn which ideas, formats and channels create real value.

## Product thesis
Generative AI reduces the cost of producing media, but abundance increases the importance of selection, originality, evidence and taste. Mecha therefore treats **content generation as one step in a larger decision loop**, not as the product itself.

**Idea → Research → Strategy → Creation → Review → Publication → Measurement → Learning**

## Initial user and market
The first user is an individual creator/operator who wants AI leverage without surrendering editorial control.

The initial content audience is primarily in **Spain**, and generated content defaults to **Spanish from Spain (`es-ES`)**. Source code and developer/architecture documentation remain in English.

## Initial content brands
Mecha initially supports two separate content products, each with its own identity and accounts on YouTube, Instagram and TikTok.

### 1. Natural Worlds
Cinematic, realistic videos that simulate drone flights over identifiable real landscapes and natural environments. Scenes may include photorealistic wildlife, but not cartoon animals. The objective is to give viewers an evocative preview of what visiting a real paradise could feel like.

The product must distinguish generated or simulated imagery from documentary footage, verify real-place facts, and avoid implying that synthetic wildlife or events were actually captured at the location.

### 2. City Walks
Immersive videos that simulate walking through real cities under different conditions, enriched with concise cultural, historical and practical context in Spanish.

A map provider may supply routes, coordinates, points of interest and permitted imagery. AI can improve pacing, remove unsuitable segments, enhance presentation and generate narration or overlays. Google Maps and Street View usage is conditional on API capabilities, attribution, licensing and derivative-work rules; Mecha must also support alternative providers or properly licensed source footage.

The brands share orchestration, research, generation, review, publishing and analytics capabilities, while preserving separate channel credentials, editorial profiles and performance histories.

## Jobs to be done
1. Capture an idea with minimal friction.
2. Determine whether it is worth developing.
3. Research it using attributable sources.
4. Find an audience, angle and suitable formats.
5. Plan a real location, route, scene or narrative.
6. Produce a strong canonical piece of content.
7. Derive platform-specific video, image, caption, audio and metadata assets.
8. Review realism, provenance, rights, safety and editorial quality.
9. Publish through supported channels.
10. Measure content, audience and eventually revenue outcomes.
11. Feed evidence back into future decisions.

## In scope
Idea/content workspace; research and provenance; two initial content brands; location and route planning; pluggable proprietary and local LLMs; pluggable image/video generation; human review; YouTube, Instagram and TikTok adapters; scheduling/publication state; normalized analytics; experimentation; monetization signals; agentic orchestration where useful; localization starting with `es-ES`.

## Not in scope initially
Fully autonomous unsupervised publishing; mass generation for volume; training foundation models; building media foundation models; scraping, recording or republishing map imagery outside provider terms; claiming synthetic footage is authentic capture; every social platform in the MVP; premature multi-tenant SaaS; hard-coding around one AI or mapping provider.

## Product principles
- **Originality over automation.**
- **Evidence over confident generation.**
- **One source, many expressions.**
- **Separate brands, shared platform.**
- **Human control at consequential boundaries.**
- **Respect rights, attribution and platform policies.**
- **Disclose simulated or materially AI-generated reality.**
- **Learn, don't merely report.**
- **Spanish-first, localization-ready.**
