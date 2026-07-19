// Design system for the whiteboard-reels visual theme.
// Scene timing is loaded from timing.json (produced by scripts/tts.py or
// scripts/tts_kokoro_onnx.py) instead of hardcoded, so this file works for ANY topic.

import * as fs from "fs";
import * as path from "path";

export const SHARD_COLORS = ["#22d3ee", "#38bdf8", "#facc15", "#fb7185", "#ec4899"];
export const SHARD_NAMES = ["SHARD 0", "SHARD 1", "SHARD 2", "SHARD 3", "NEW SHARD"];

export const COLORS = {
  bg: "#000000",
  white: "#ffffff",
  red: "#ef4444",      // danger / nightmare / "+1 SHARD"
  blue: "#38bdf8",     // solution title color
  green: "#22c55e",    // success checkmarks
  gray: "#9ca3af",
};

// Font families (load via @remotion/google-fonts at module scope in Root.tsx)
export const FONT_MARKER = "'Permanent Marker', 'Patrick Hand', cursive";
export const FONT_HAND = "'Patrick Hand', cursive";
export const FONT_SANS = "'Nunito', sans-serif";

export const FPS = 30;

// ---- Scene timing: load from timing.json (audio-driven) ----
// timing.json shape: { "s1": {start, duration, end}, ... } in seconds.
// Falls back to empty if missing (render will be wrong, but won't crash import).
type Timing = Record<string, { start: number; duration: number; end: number }>;

function loadTiming(): Timing {
  // Look in a few likely locations relative to the project.
  // Include the FLAT audio/timing.json path — gen_kokoro / kokoro_onnx writes there,
  // not under an engine subdir. Missing this path silently yields a wrong-length render.
  const candidates = [
    path.join(__dirname, "..", "audio", "timing.json"),
    path.join(__dirname, "..", "audio", "elevenlabs", "timing.json"),
    path.join(__dirname, "..", "audio", "kokoro", "timing.json"),
    path.join(process.cwd(), "audio", "timing.json"),
    path.join(process.cwd(), "audio", "elevenlabs", "timing.json"),
    path.join(process.cwd(), "audio", "kokoro", "timing.json"),
  ];
  for (const c of candidates) {
    try {
      if (fs.existsSync(c)) return JSON.parse(fs.readFileSync(c, "utf8"));
    } catch { /* try next */ }
  }
  return {};
}

const TIMING = loadTiming();

// Scene start/end in FRAMES (converted from seconds).
export const SCENES: Record<string, [number, number]> = Object.fromEntries(
  Object.entries(TIMING).map(([k, v]) => [
    k,
    [Math.round(v.start * FPS), Math.round(v.end * FPS)] as [number, number],
  ])
);

// Total narration duration in seconds (max end + 0.8s tail), fallback 10s.
const maxEnd = Object.values(TIMING).reduce((m, v) => Math.max(m, v.end), 0);
export const DURATION_SEC = maxEnd > 0 ? maxEnd + 0.8 : 10;

// Helper: persistence progress for a scene across [drawStart, drawEnd] within that scene.
// Returns 0 before the scene, animates 0->1 across the draw window, then 1 forever after.
export function pers(
  frame: number,
  sceneId: string,
  drawStartFrac = 0.05,
  drawEndFrac = 0.55
): number {
  const range = SCENES[sceneId];
  if (!range) return 0;
  const [s, e] = range;
  if (frame < s) return 0;
  const ds = s + (e - s) * drawStartFrac;
  const de = s + (e - s) * drawEndFrac;
  if (frame >= de) return 1;
  if (frame <= ds) return 0;
  return Math.max(0, Math.min(1, (frame - ds) / (de - ds)));
}
