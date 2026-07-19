# whiteboard-reels

A [skills.sh](https://skills.sh) skill that produces **hand-drawn "digital whiteboard / scribe"-style explainer Reels** — vertical (1080×1920) educational videos about system-design and backend topics, all sharing one visual identity but each with its own original diagrams and script.

Built around a real working pipeline: Remotion + ElevenLabs Brian TTS (Kokoro fallback) + **mimo-v2.5 as the validity gate** via opencode zen. The build is only "done" when mimo says so.

## What it does

Give it a topic. It ships a finished, mimo-verified Reels video:

```
topic
  → script.json        (title / headline / ~15-18 scene beats)
  → TTS                (ElevenLabs Brian, Kokoro fallback on quota exhaustion)
  → Remotion scenes    (self-drawing persistent-canvas animation, original per topic)
  → render 360×640
  → VERIFY with mimo:
      ├── 6 single-focus checks (one constrained question each — reliable)
      └── 1 whole-video defect scan (gate = "NO DEFECTS FOUND")
  → auto-fix loop until clean (cap 8 rounds), every version preserved
  → render Reels 1080×1920
```

## The look
- Pure black canvas, white self-drawing strokes (stroke-dashoffset, like a tablet pen)
- Elements **accumulate on a persistent canvas** — never relayout when a new one is added
- Permanent Marker + Nunito fonts, red/blue/green accent stamps
- Problem chapter → clear-to-black → solution chapter, ~150-165s, audio-driven timing

## Install

Install into all your agents (Claude Code, Codex, Cursor, OpenCode, and [70+ more](https://skills.sh)):

```bash
npx skills add MamounHisham1/whiteboard-reels
```

Install into a specific agent only:

```bash
npx skills add MamounHisham1/whiteboard-reels -a claude-code
```

Install globally (available across all projects):

```bash
npx skills add MamounHisham1/whiteboard-reels -g
```

Use it once without installing:

```bash
npx skills use MamounHisham1/whiteboard-reels
```

Manual install (clone into your agent's skills dir):

```bash
# Claude Code / ZCode
git clone https://github.com/MamounHisham1/whiteboard-reels /tmp/wbr && \
  cp -r /tmp/wbr/skills/whiteboard-reels ~/.claude/skills/
```

## Requirements
- `node`, `npx remotion`, `python3`, `ffmpeg`/`ffprobe`
- Environment (no secrets are hardcoded in this skill — see `skills/whiteboard-reels/references/setup.md`):
  - `OPENCODE_KEY` — bearer token for mimo-v2.5 via opencode zen (required for verification). Get it: https://opencode.ai/zen
  - `ELEVENLABS_API_KEY` — for Brian voice (falls back to Kokoro if unset/exhausted). Get it: https://elevenlabs.io
  - `ELEVEN_VOICE` — optional, default `nPczCjzI2devNBz1zQrb` (Brian, a public preset voice)
  - `KOKORO_PYTHON` / `KOKORO_ONNX_MODEL` / `KOKORO_ONNX_VOICES` — optional, only needed for the Kokoro fallback. No defaults; you point them at your local Kokoro install.

## Quick start
```bash
export OPENCODE_KEY=sk-...
export ELEVENLABS_API_KEY=sk_...

python3 skills/whiteboard-reels/scripts/scaffold.py my-topic --headline "MY TOPIC"
# edit videos/my-topic/script.json (write ~15-18 scene beats)
python3 skills/whiteboard-reels/scripts/tts.py my-topic
# write videos/my-topic/remotion-project/src/scenes/Chapter1.tsx etc.
cd videos/my-topic/remotion-project && npm install
npx remotion render <Composition> out/video.mp4
python3 skills/whiteboard-reels/scripts/save_version.py my-topic
python3 skills/whiteboard-reels/scripts/mimo_full.py out/video.mp4 my-topic
```

See `skills/whiteboard-reels/SKILL.md` for the full workflow and `skills/whiteboard-reels/references/` for the design language, build pipeline, and the mimo verification protocol.

## Why not the cloud `remotion-render` skill?
The bundled `remotion-render` skill renders raw TSX via a cloud CLI. That's great for one-off animations, but the whiteboard look needs a full local project (bundled Primitives, palette, fonts, audio-driven timing, saved versions). This skill bundles those as `assets/` and uses `npx remotion render` locally. See `references/remotion-render-note.md`.

## License
MIT
