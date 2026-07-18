---
name: whiteboard-reels
description: "Make hand-drawn whiteboard-style explainer Reels videos (system-design / educational topics) that match a reference visual theme exactly. Full pipeline per video: script.json -> ElevenLabs Brian TTS (Kokoro fallback) -> Remotion scenes with self-drawing persistent-canvas animation -> render 360x640 -> mimo AI verification loop (single-focus per-issue checks + final whole-video scan, auto-fix until clean) -> save every version -> render 1080x1920 Reels. Use when the user wants to create, rebuild, fix, or batch-produce whiteboard/scribe educational videos, system-design explainers, or reels matching a reference. Triggers: whiteboard video, scribe video, explainer reel, system design reel, remotion educational video, mimo verify video, content series, batch produce videos."
metadata:
  version: 1.0.0
  author: MamounHisham1
  skills_sh: true
---

# Whiteboard Reels

Produce a series of hand-drawn "digital whiteboard / scribe" explainer Reels. Each video is **one topic** matching a fixed visual identity (palette, fonts, animation mechanics, voice), but with its **own original diagrams and script** — never a template copy.

The look: black canvas, strokes that draw themselves in (like a tablet pen), elements that **accumulate on a persistent canvas** (never relayout when a new element is added), clear-to-black between chapters, red NIGHTMARE stamp + green check resolution.

## What this skill depends on

**Required runtime:** `node`, `npx remotion`, `python3`, `ffmpeg`/`ffprobe`, `curl`.

**Remotion skill (optional helper):** This skill loads `remotion-render` if present. Check first:
```bash
ls ~/.zcode/skills/remotion-render ~/.agents/skills/remotion-render ~/.claude/skills/remotion-render 2>/dev/null
```
If missing in all three, install from the official registry or skip it — rendering here uses a **local `remotion-project/`** (your own Primitives + theme + fonts), NOT the cloud `belt` CLI. The local project is what produces reference-fidelity output. See `references/remotion-render-note.md`.

## Required environment (NO secrets in this skill)

This skill ships with NO hardcoded keys. You must set two env vars before building. See
`references/setup.md` for where to get each key and how to persist it.

- `OPENCODE_KEY` — **required**. Bearer token for mimo-v2.5 via opencode zen (the verification gate). Get it: https://opencode.ai/zen
- `ELEVENLABS_API_KEY` — **required for Brian voice**. Get it: https://elevenlabs.io (free tier = 10k chars/mo). Falls back to Kokoro if unset, but Kokoro only works if installed locally (see setup.md).
- `ELEVEN_VOICE` (optional) — voice id, default `nPczCjzI2devNBz1zQrb` (Brian).
- `KOKORO_PYTHON` (optional) — kokoro-capable python for the fallback, default `/tmp/kokoro-env/bin/python3`.

Quick setup:
```bash
cp skills/whiteboard-reels/.env.example .env   # then edit .env with your keys
set -a; source .env; set +a
python3 skills/whiteboard-reels/scripts/check_env.py   # verify before building
```

## The flow (per video)

0. **Check env** — `python3 scripts/check_env.py`. If `OPENCODE_KEY` or `ELEVENLABS_API_KEY` is missing, **stop and tell the user** — show them `references/setup.md` and the `export` commands. Do NOT proceed to scaffold until required vars are set.
1. **Scaffold** — `scripts/scaffold.py <slug>` creates `videos/<slug>/` with `script.json` template + `remotion-project/` seeded from `assets/` (Primitives.tsx, theme.ts, package.json, public/).
2. **Write the script** — edit `script.json`: `{title:"SYSTEM DESIGN", headline:"<TOPIC>", voice:"<id>", scenes:[{id,text}...]}`. Aim 15-18 scenes, ~150-165s narration. Follow `references/script-template.md` for the narrative arc.
3. **Generate TTS** — `scripts/tts.py <slug>` → per-scene audio + `timing.json` + `full_narration.mp3`. Tries ElevenLabs Brian first; on quota/HTTP error, auto-falls back to Kokoro `am_michael` and prints `VOICE_USED=am_michael`.
4. **Write the Remotion scenes** — original diagrams for THIS topic. Copy font-loading + dependency set from the reference project. See `references/design-language.md` (exact palette, fonts, animation mechanics) and `references/build-pipeline.md`.
5. **Render 360x640** — `npx remotion render <composition> out/video.mp4`. Save a versioned copy: `cp out/video.mp4 remotion-project/versions/video_v1.mp4` (see `scripts/save_version.py`).
6. **Verify with mimo** — `references/mimo-verification.md`. Run six **single-focus** checks, then one **whole-video** scan. Auto-fix + re-render until whole-video returns `NO DEFECTS FOUND` or the cap is hit.
7. **Render Reels 1080x1920** — `npx remotion render <composition> reels/<slug>_reels.mp4 --scale 3`.

## The verification loop (core of this skill)

For each rendered video, run BOTH:

**A. Per-issue single-focus checks** (`scripts/mimo_check.py`) — one constrained question per call. These are reliable (free-form whole-video rubrics are not). The six checks:
1. persistent-canvas (elements don't relayout when a new one is added)
2. self-drawing strokes (stroke-dashoffset pen motion, nothing pops)
3. vertical-fill (top third not empty, content not all stacked at the bottom)
4. arrow-targeting (arrows land on their target shapes, not empty space)
5. text-legibility (no overlap/clipping/text-on-shape)
6. theme-match (palette/fonts/black-canvas match the reference)

**B. Whole-video defect scan** (`scripts/mimo_full.py`) — sends the ENTIRE mp4 as a `video_url` data URL. Returns severity-ranked defects with timestamps. Gate = `NO DEFECTS FOUND`.

**NEVER** cut the video into PNG frames for mimo. Always send the whole mp4. This is the single most important method rule.

**Fix loop:** until whole-video says clean OR cap (default 8 rounds) is hit. Each round: read defects → fix the exact elements named → save a new version (`video_vN.mp4`) → re-verify. **Never overwrite a version** — the user watches all versions.

## Batch production

To build N videos: dispatch N sub-agents (one per topic), each running steps 1-7 independently. The user monitors actively and will interrupt if something is off. **Do not** silently fall back to serial bash when sub-agents were requested.

## Critically — how to work with the user

Read `references/user-style.md` once. Short version: work immediately (no ceremony), send whole videos to mimo (never frames), fix the exact element the user names (not a neighbor), kill+retry hung mimo calls fast, and preserve every render version.

## File map

- `SKILL.md` — this file.
- `references/design-language.md` — exact palette, fonts, animation mechanics, narrative arc.
- `references/build-pipeline.md` — Remotion project layout, render commands, version-saving.
- `references/mimo-verification.md` — the verification protocol in detail.
- `references/script-template.md` — script.json structure + scene-by-scene narrative template.
- `references/remotion-render-note.md` — why we use a local project, not the cloud belt CLI.
- `references/user-style.md` — working-style notes for this skill's user.
- `scripts/scaffold.py` — create a new video folder + seed the Remotion project.
- `scripts/tts.py` — ElevenLabs Brian → Kokoro fallback, with timing.json.
- `scripts/mimo_check.py` — single-focus mimo check (one of 6 categories).
- `scripts/mimo_full.py` — whole-video mimo defect scan.
- `scripts/save_version.py` — copy out/video.mp4 to versions/video_vN.mp4.
- `assets/Primitives.tsx` — self-drawing animation primitives (Cylinder, DrawLine, Clock12, ...).
- `assets/theme.ts` — palette, fonts, scene-timing loader.
- `assets/package.json` — pinned dependency set for the Remotion project.
