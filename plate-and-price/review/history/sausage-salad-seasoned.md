# Review history: sausage-salad-seasoned (Seasoned Sausage and Tomato Salad)

Scores out of 10 from the seven reviewer agents (AI reviewers working from contact sheets, facts and the voice script; they cannot listen). Language-sensitive agents scored English and Spanish separately; engagement and craft scored the shared cut once. Three rounds were run before the owner reduced the rule to two rounds (directive 19 now says two).

## Averages (short EN / short ES / video EN / video ES)
| Round | Short EN | Short ES | Video EN | Video ES | What changed before this round |
|---|---|---|---|---|---|
| 1 | 6.0 | 5.9 | 5.9 | 5.7 | Baseline: 17 clips of about 1.8 s (35.7 s) without voice, 88 s video, 10-row price card (overlapping), first AI cover |
| 2 | 6.6 | 6.6 | 6.4 | 6.4 | Pour hook, honey/peel/browning/bubbling shots, 8-row price card, new AI cover, voice-over in both formats, first speed-ups |
| 3 | 7.4 | 7.4 | 7.2 | 7.2 | Browned-pieces shot, repeat pour removed from the short, more speed-ups, pan-oil step, ducked music, price list trimmed to 5.00 EUR |
| final tweak | not reviewed | | | | Short ending cut to 2.0 s, honey shot shortened, video ending on one steady plate with its line, cover line "under three euros a plate", ginger window, music release 800 ms (short 35.2 s, video 78.3 s) |

## Per agent, round 3 (EN / ES)
| Agent | Short | Video |
|---|---|---|
| audience-sociologist | 7.5 / 7.5 | 7.5 / 7.5 |
| marketing-strategist | 7 / 7 | 6.5 / 6.5 |
| recipe-price-checker | 7.5 / 7.5 | 8 / 8 |
| discoverability-strategist | 7.5 / 7.5 | 7.5 / 7.5 |
| audio-voice-reviewer | 7 / 7 | 7 / 7 |
| engagement-analyst (shared) | 8 | 7 |
| video-craft-editor (shared) | 7 | 7 |

## Decision log
| Round | Agent | Fix (lever) | Decision | Reason or where it landed |
|---|---|---|---|---|
| 1 | recipe-price, marketing, sociologist, engagement, craft | [price] end card overlaps (10 rows) | applied | price.json merged to 8 rows |
| 1 | audio | [audio] tempo_max 1.0 | applied | owner rule: voice never sped up |
| 1 | marketing, sociologist, discoverability, recipe-price | [captions] "caldo" is wrong, "Lava" not "Lavamos" | applied | video.json |
| 1 | sociologist, marketing, engagement | [shots] hook = pan juices pour | applied | hook segment |
| 1 | craft, engagement | [shots] add honey, browning, peeling, bubbling, ginger readable | applied | segments |
| 1 | marketing, sociologist, discoverability | [cover] cover shows a different sausage | applied twice | AI cover regenerated; still crumbs/coins (AI limit, accepted) |
| 1 | discoverability | [text] remove #Shorts from the title | declined | channel convention |
| 1 | discoverability | [text] change the title to "tomate aliñado" | declined | title is the owner's; noted for the owner |
| 1 | engagement, sociologist | [shots] end on the hook-like loop shot | declined | price end card is the channel's promise |
| 1 | audio | [audio] pan sizzle | declined | original kitchen sound is removed on purpose |
| 2 | audio | [audio] duck the music under the voice | applied | sidechain compression in edit_short.py |
| 2 | audio | [captions] full stops / varied gaps | declined | captions drive both text and voice; lines follow the cuts |
| 2 | engagement, craft, sociologist | [shots] speed up slow moments, drop the repeat pour | applied | segments[].speed, short without the repeat |
| 2 | recipe-price | [price] tomatoes 2.00, sausages 1.40, oil and honey 0.50; drop oregano | applied | price.json, recipe.md (total 5.00, 2.50 a serving) |
| 2 | recipe-price | [shots] add GH011613 (oil and a spoon of dressing) | applied in the video, not in the short | short too long |
| 2 | marketing, sociologist | [captions] hook caption with the price | declined | the price is on the cover card right after |
| 2 | discoverability | [text] playlist line | declined | the channel has no playlist yet |
| 3 | craft, engagement, marketing, sociologist | [shots] cut the final short shot, one steady ending in the video | applied | tweak after round 3 |
| 3 | audio | [captions] cover line repeats "two" | applied | "Under three euros a plate" |
| 3 | craft | [picture] reframe the honey shot higher | declined | vertical crop only moves sideways (cx); the shot was shortened instead |
| 3 | all | [audio] replace "September" | open | owner decision; needs a licensed or royalty-free track |

Not reviewed after the final tweak. Open: the AI cover still looks like crumbs; the song is unlicensed; nothing has been pushed.

## Short with AI (short_ia, Spanish only): rounds 1 and 2
New product made after the owner's rules for longer shorts (no length limit), non-centred crops, zoom, speed, and AI upscaling (directives 27-31). Seven agents, Spanish only (two rounds, the owner's rule).

| Round | Sociologist | Marketing | Recipe-price | Discoverability | Audio-voice | Engagement | Craft | Average | What changed before this round |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 6 | 6 | 7 | 6 | 6 | 6 | 6 | 6.1 | 24 moments, 56 s, cx per clip, two blurpad zoom-outs, AI upscale, voice, first AI cover |
| 2 | 7.5 | 7 | 8 | 7 | 7 | 7 | 7 | 7.2 | Blurpads replaced by fill crops, garlic/onion/lemon/honey framed, new cover, hook line names the dish, end line spoken, no repeat of the hook |
| final tweak | not reviewed | | | | | | | | Onion and final plate retimed, pour reframed, "Bien dorada", spoken price "dos con cincuenta cada uno" (end card 5.5 s), "cena barata" tag removed |

Decision log (short_ia): blurpad shots dropped for fill crops (marketing, sociologist, engagement, craft, applied); cover regenerated three times (applied, a first try produced walnuts, then browned chunks); "Aceite y aliño" and "Sal gorda" kept (key steps, declined); pan-sizzle / kitchen sound declined; AI vs plain resize judged by the critics: small gain (crisper edges and bubbles, no artifacts). Open: unlicensed song; the final plate cannot be shown whole in a vertical slice.
