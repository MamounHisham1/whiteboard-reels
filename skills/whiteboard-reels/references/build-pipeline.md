# Build Pipeline (per video)

## Project layout
```
videos/<slug>/
├── script.json                      # title, headline, voice, scenes[]
├── audio/
│   └── elevenlabs/                  # per-scene mp3/wav, timing.json, full_narration.mp3
│       └── (or audio/kokoro/ if fallback ran)
└── remotion-project/
    ├── package.json                 # pinned deps (see assets/package.json)
    ├── public/
    │   └── narration.mp3            # copy of full_narration.mp3
    ├── src/
    │   ├── index.ts                 # registerRoot
    │   ├── Root.tsx                 # <Composition> with FPS + duration
    │   ├── theme.ts                 # palette, fonts, SCENES timing (load from timing.json)
    │   ├── Video.tsx                # main composition, picks active chapter by frame
    │   ├── components/Primitives.tsx# bundled self-drawing primitives (assets/Primitives.tsx)
    │   └── scenes/
    │       ├── Chapter1.tsx         # PROBLEM chapter — original diagrams for THIS topic
    │       ├── TitleCard.tsx        # clear-to-black + headline stamp
    │       └── Chapter2.tsx         # SOLUTION chapter — original diagrams for THIS topic
    ├── out/
    │   └── video.mp4                # latest 360x640 render
    ├── versions/
    │   └── video_v1.mp4, video_v2.mp4, ...   # EVERY saved version, never overwritten
    └── reels/
        └── <slug>_reels.mp4         # final 1080x1920 deliverable
```

## Render commands

**Dev preview:**
```bash
cd videos/<slug>/remotion-project && npx remotion studio
```

**Render 360x640 (working copy):**
```bash
cd videos/<slug>/remotion-project
npx remotion render <CompositionId> out/video.mp4
```

**Save a version (never skip — the user watches all versions):**
```bash
python3 <skill>/scripts/save_version.py videos/<slug>
# -> versions/video_v<N+1>.mp4
```

**Reels-quality final (1080x1920 via --scale 3):**
```bash
cd videos/<slug>/remotion-project
mkdir -p reels
npx remotion render <CompositionId> reels/<slug>_reels.mp4 --scale 3
```

## Timing derivation
- `timing.json` is produced by `scripts/tts.py` and records `{scene_id: {start, duration, end}}`
  in seconds, derived from real `ffprobe` durations of each scene's wav, with 0.12s gaps.
- `theme.ts` loads timing.json at build time and converts to frames (`Math.round(sec * 30)`).
- `DURATION_SEC` = total narration length + ~0.8s tail. `Root.tsx` uses
  `Math.round(DURATION_SEC * 30)` as the composition duration.

## Wiring audio + scenes
- Copy `audio/.../full_narration.mp3` to `remotion-project/public/narration.mp3`.
- In `Video.tsx`: `import { Audio, staticFile } from "remotion"` then
  `<Audio src={staticFile("/narration.mp3")} />` at the top level.
- Each scene reads its frame range from `SCENES[sceneId]` (in theme.ts) and renders its
  primitives with `progress` derived from the local frame position.

## Writing ORIGINAL scenes (do not template-copy)
- Study `assets/Primitives.tsx` for the available self-drawing primitives.
- Design diagrams specific to your topic (a Bloom filter is bit-arrays + hash arrows; rate
  limiting is a token bucket + leaking; LSM trees are stacked memtable+SSTables; etc.).
- Choose fixed coordinates up front. The canvas is 360x640 — plan the layout across all
  three vertical thirds before writing a single `<g>`.
- When in doubt about how a mechanic should look, consult the verification output (the
  per-issue mimo checks will tell you if layout/arrow-targeting/persistence is wrong).
