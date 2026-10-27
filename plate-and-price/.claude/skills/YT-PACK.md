# YouTube skill pack (third party)

Installed from https://github.com/Jakeschincariol/youtube-agent-skill (commit a2feb21, 2026-09-16), MIT licence (see
LICENSE-youtube-agent-skill). Nine of its eleven skills are installed; the code was read before installing: six Python scripts, standard
library only, no network, no commands run, files are only read.

| Skill | What it is for here |
|---|---|
| yt-retention | read a YouTube Studio retention export of a published video: hook leak, cliffs, slide |
| yt-chapters | check chapters against YouTube's rules (starts at 0:00, at least 3, each at least 10 s) |
| yt-package | lint a title and thumbnail text pair (60 and 40 character cuts, no repeated words, 3 words on the thumbnail) |
| yt-edit | dead air, filler and retakes from a transcript of the spoken recordings, as an edit decision list |
| yt-script | hook formulas (21) and a hook scorer; used to score the hook line of a short or video |
| yt-viral | rank what works in the niche by how far each video beats its own channel's median (public data only) |
| yt-plan | weekly upload plan sized to the owner's time |
| yt-audit | whole-channel review that ends in one fix |
| yt-comment | triage comments and draft short replies in the channel voice (the owner posts them) |

Not installed: yt-seo (the discoverability critic and make_description.py already do it; only its "query test" was added to the critic)
and yt-shorts (shorts here are made from the recordings, not cut from a long video).

Changes to the originals: the voice profile path is `brand/voice.md` instead of `~/.claude/youtube/voice.md`, and yt-plan says shorts are
made by this pipeline. How they fit the pipeline: CLAUDE.md directive 32. None of the skills publishes anything.
