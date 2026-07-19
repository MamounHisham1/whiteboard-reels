# Shared Visual Design Language

The ONLY things shared across videos — the *look*. Each video has its OWN topic, script,
scenes, shapes, and animation choreography. Never copy another video's content or scene
structure; invent original diagrams that fit your topic.

## Canvas
- Composition: 360 x 640 (9:16 portrait), 30 fps. Final Reels render: 1080 x 1920 (`--scale 3`).
- Background: pure black `#000000`.
- SVG viewBox `"0 0 360 640"`, `preserveAspectRatio="xMidYMid meet"`.
- Distribute content across ALL THREE vertical thirds (top / mid / bottom). NEVER leave the
  top empty while content stacks at the bottom. Keep a persistent title/chapter header in
  the top third throughout each chapter.

## Palette (exact — see assets/theme.ts)
- Lines / default ink: white `#ffffff`
- Danger / problem / stamps: red `#ef4444`
- Solution / positive titles: blue `#38bdf8`
- Success / checkmarks: green `#22c55e`
- Muted labels: gray `#9ca3af`
- Category accents (reuse this family): cyan `#22d3ee`, blue `#38bdf8`, yellow `#facc15`,
  pink `#fb7185` / `#ec4899`

## Typography
- Marker / titles / stamps: **Permanent Marker** (handwritten). Load via
  `@remotion/google-fonts/PermanentMarker`.
- Body / labels / formula: **Nunito** 800. Load via `@remotion/google-fonts/Nunito`.
- Hand notes (optional): **Patrick Hand**.
- Load fonts at module scope: `import * as PM from "@remotion/google-fonts/PermanentMarker"; PM.loadFont();`
  Call `loadFont()` BARE — no options — passing options throws `"does not have a style"`.

## Animation mechanics (the whiteboard/scribe feel)

**Self-drawing:** EVERY element draws itself progressively via `stroke-dashoffset` (a "pen
moving"). Nothing pops in. Use `pathLength={1000} strokeDasharray={1000}
strokeDashoffset={1000 * (1 - progress)}`.

**Persistent canvas:** once an element is drawn it STAYS. Use a helper like:
```ts
function pers(sceneId: string, drawStart: number, drawEnd: number): number {
  const [s, e] = SCENES[sceneId];
  // returns 0 before the scene, animates 0->1 across [drawStart,drawEnd] within scene, then 1 forever
}
```
Elements accumulate on one canvas. They NEVER move, resize, or relayout once placed. Fixed
coordinates. This is THE core mechanic — when adding the Nth element to a set, the existing
N-1 must not shift.

**Additive layering** within a chapter. Between chapters: a HARD CLEAR-TO-BLACK (fade the
old canvas out, blank black, then the new diagram draws fresh). No wipes/morphs within a scene.

**Hand-drawn wobble:** jitter path points by +/-1.5..5px deterministically (seeded). Circles
drawn as a 24-sided polygon with radius wobble so they read as sketchy, not geometric. See
`assets/Primitives.tsx` `Clock12` and `w()`.

**Laying out a growing set:** when adding an Nth element (shards, nodes, buckets), lay out
all N slots from the start with fixed coordinates and fill them one by one — the existing
ones stay put. Optionally show a faint dashed placeholder for the next slot.

## Narrative arc (match the reference's rhythm)
- A **PROBLEM** chapter: problem -> why it's hard -> a NIGHTMARE/worst-case moment with a
  red stamp (`#ef4444`, Permanent Marker, ~62px, slight rotation) + chaos arrows.
- A hard clear-to-black.
- A **SOLUTION** chapter: the clean technique that resolves it, ending with a green
  checkmark (`#22c55e`) + a closing one-liner.
- ~150-165s total, 15-18 narration scenes, audio-driven timing.

## Voice
- ElevenLabs voice "Brian" id `nPczCjzI2devNBz1zQrb`, model `eleven_multilingual_v2`.
- English. Same voice across the whole series for consistency. Kokoro `am_michael` is a
  fallback ONLY when ElevenLabs quota is exhausted — flag it loudly when it happens.
