# Build Pipeline (per video)

## Project layout
```
videos/<slug>/
├── script.json                      # title, headline, voice, scenes[]
├── audio/                           # per-scene wav, timing.json, full_narration.mp3/.wav
│   │                                #   tts_kokoro_onnx.py writes here FLAT (no subdir)
│   └── elevenlabs/ | kokoro/        #   tts.py writes under an engine subdir instead
│                                    # theme.ts loadTiming() checks audio/timing.json FIRST,
│                                    #   then the engine subdirs
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

**Save a version (never skip — every render is preserved for review):**
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
- `timing.json` is produced by `scripts/tts.py` (engine subdir) or `scripts/tts_kokoro_onnx.py`
  (flat `audio/`), recording `{scene_id: {start, duration, end}}` in seconds, derived from real
  per-scene wav durations with 0.12s gaps.
- Most scene `theme.ts` files load `timing.json` at build time (see `assets/theme.ts`
  `loadTiming()`, which now checks the flat `audio/timing.json` path first). If a topic's
  `theme.ts` instead hardcodes an inline `const timing = {...}` table, regenerate it from the
  real audio with `scripts/patch_theme_timing.py <slug>` after running TTS.
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
- Design diagrams specific to your topic (a token bucket + leaking for rate limiting; stacked
  memtable + SSTables for LSM trees; bit-arrays + hash arrows for a Bloom filter; etc.).
- Choose fixed coordinates up front. The canvas is 360x640 — plan the layout across all
  three vertical thirds before writing a single `<g>`.
- When in doubt about how a mechanic should look, consult the verification output (the
  per-issue mimo checks will tell you if layout/arrow-targeting/persistence is wrong).
