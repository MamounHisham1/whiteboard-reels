import React from "react";
import { COLORS, FONT_SANS } from "../theme";

// ============================================================================
// HAND-DRAWN / SELF-DRAWING ANIMATION PRIMITIVES
// Everything draws itself progressively (stroke-dashoffset) like a tablet pen.
// Core principle: an element's (x,y) is FIXED. progress only grows 0->1 then
// stays 1. Nothing ever moves or rescales once drawn — that is what makes the
// canvas read as "persistent / additive" instead of "cut to a new picture".
// ============================================================================

// Deterministic pseudo-random in [-1,1] from a seed + index.
function rand(seed: number, n: number): number {
  const x = Math.sin(seed * 9999.1 + n * 17.3) * 10000;
  return (x - Math.floor(x)) * 2 - 1;
}

// ---------- Wobble a numeric coordinate by a small deterministic jitter ----------
// amp ~ px of hand-drawn wobble. seed must be unique per element.
function w(seed: number, n: number, amp = 1.4): number {
  return rand(seed, n) * amp;
}

// ---------- DashDraw: a path that draws itself via stroke-dashoffset ----------
export const DashDraw: React.FC<{
  d: string; progress?: number; color?: string; width?: number;
}> = ({ d, progress = 1, color = COLORS.white, width = 2.5 }) => {
  const len = 1000;
  return (
    <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round"
      pathLength={len}
      strokeDasharray={len}
      strokeDashoffset={len * (1 - progress)} />
  );
};

// ---------- Self-drawing circle (stroke-draw) ----------
export const DrawCircle: React.FC<{
  cx: number; cy: number; r: number; progress?: number; color?: string; width?: number;
}> = ({ cx, cy, r, progress = 1, color = COLORS.white, width = 2.5 }) => (
  <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={width}
    pathLength={1000} strokeDasharray={1000} strokeDashoffset={1000 * (1 - progress)} strokeLinecap="round" />
);

// ---------- Self-drawing ellipse (with optional wobble) ----------
export const DrawEllipse: React.FC<{
  cx: number; cy: number; rx: number; ry: number; progress?: number; color?: string; width?: number; seed?: number;
}> = ({ cx, cy, rx, ry, progress = 1, color = COLORS.white, width = 2.5, seed = 0 }) => {
  if (seed) {
    // approximate wobble by a small path instead of perfect ellipse
    const wx = rx + w(seed, 1, 1.0), wy = ry + w(seed, 2, 0.8);
    const d = `M ${cx - wx} ${cy} A ${wx} ${wy} 0 1 0 ${cx + wx} ${cy} A ${wx} ${wy} 0 1 0 ${cx - wx} ${cy} Z`;
    return <DashDraw d={d} progress={progress} color={color} width={width} />;
  }
  return (
    <ellipse cx={cx} cy={cy} rx={rx} ry={ry} fill="none" stroke={color} strokeWidth={width}
      pathLength={1000} strokeDasharray={1000} strokeDashoffset={1000 * (1 - progress)} strokeLinecap="round" />
  );
};

// ---------- Self-drawing line ----------
export const DrawLine: React.FC<{
  x1: number; y1: number; x2: number; y2: number; progress?: number; color?: string; width?: number;
}> = ({ x1, y1, x2, y2, progress = 1, color = COLORS.white, width = 2.5 }) => (
  <line x1={x1} y1={y1} x2={x1 + (x2 - x1) * progress} y2={y1 + (y2 - y1) * progress}
    stroke={color} strokeWidth={width} strokeLinecap="round" />
);

// ---------- Self-drawing cylinder (database). Stroke-draws outline, then fill ----------
// x,y = top-center. r = radius. h = height. FIXED position; never re-laid-out.
export const Cylinder: React.FC<{
  x: number; y: number; r: number; h: number; color?: string; fill?: number; label?: string;
  drawProgress?: number; fillProgress?: number; filled?: boolean; seed?: number;
}> = ({ x, y, r, h, color = COLORS.white, fill = 0, label, drawProgress = 1, fillProgress, filled, seed = 0 }) => {
  const ry = r * 0.32;
  const fProg = fillProgress !== undefined ? fillProgress : drawProgress;
  const fillH = (fill / 100) * h;
  const showFill = (filled || fill > 0) && fProg > 0.5 ? (fProg - 0.5) / 0.5 : 0;
  const s = seed || Math.abs(Math.round(x * 13 + y * 7));
  return (
    <g>
      {/* side lines draw first */}
      <DrawLine x1={x - r} y1={y} x2={x - r} y2={y + h} progress={Math.min(drawProgress * 2, 1)} color={color} width={2} />
      <DrawLine x1={x + r} y1={y} x2={x + r} y2={y + h} progress={Math.max(0, Math.min((drawProgress - 0.1) * 2, 1))} color={color} width={2} />
      {/* bottom ellipse */}
      <DrawEllipse cx={x} cy={y + h} rx={r} ry={ry} progress={Math.max(0, Math.min((drawProgress - 0.2) * 2.2, 1))} color={color} width={2} seed={s + 1} />
      {/* fill */}
      {showFill > 0 && (
        <path
          d={`M ${x - r} ${y + h - fillH * showFill}
              L ${x - r} ${y + h} A ${r} ${ry} 0 0 0 ${x + r} ${y + h}
              L ${x + r} ${y + h - fillH * showFill} A ${r} ${ry} 0 1 1 ${x - r} ${y + h - fillH * showFill} Z`}
          fill={filled ? COLORS.gray : color} opacity={0.75 * showFill}
        />
      )}
      {/* top ellipse last */}
      <DrawEllipse cx={x} cy={y} rx={r} ry={ry} progress={Math.max(0, Math.min((drawProgress - 0.35) * 2.2, 1))} color={color} width={2.5} seed={s} />
      {label && drawProgress > 0.85 && (
        <text x={x} y={y + h + ry + 22} textAnchor="middle" fill={color}
          fontFamily={FONT_SANS} fontSize={15} fontWeight={800} opacity={(drawProgress - 0.85) / 0.15}>{label}</text>
      )}
    </g>
  );
};

// ---------- Stick figure user (draws in) ----------
export const User: React.FC<{
  x: number; y: number; color?: string; scale?: number; name?: string; id?: string; drawProgress?: number;
}> = ({ x, y, color = COLORS.white, scale = 1, name, id, drawProgress = 1 }) => {
  const p = drawProgress;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} opacity={Math.min(p * 2, 1)}>
      {p > 0 && <DrawEllipse cx={0} cy={-22} rx={8} ry={8} progress={Math.min(p * 2.5, 1)} color={color} width={2.5} />}
      {p > 0.2 && <DrawLine x1={0} y1={-14} x2={0} y2={6} progress={Math.min((p - 0.2) * 2.5, 1)} color={color} width={2.5} />}
      {p > 0.4 && <>
        <DrawLine x1={0} y1={-6} x2={-10} y2={2} progress={Math.min((p - 0.4) * 2.5, 1)} color={color} width={2.5} />
        <DrawLine x1={0} y1={-6} x2={10} y2={2} progress={Math.min((p - 0.4) * 2.5, 1)} color={color} width={2.5} />
      </>}
      {p > 0.6 && <>
        <DrawLine x1={0} y1={6} x2={-8} y2={20} progress={Math.min((p - 0.6) * 2.5, 1)} color={color} width={2.5} />
        <DrawLine x1={0} y1={6} x2={8} y2={20} progress={Math.min((p - 0.6) * 2.5, 1)} color={color} width={2.5} />
      </>}
      {name && p > 0.8 && <text x={0} y={36} textAnchor="middle" fill={color} fontFamily={FONT_SANS} fontSize={14} fontWeight={800} opacity={(p - 0.8) / 0.2}>{name}</text>}
      {id && p > 0.9 && <text x={0} y={52} textAnchor="middle" fill={COLORS.gray} fontFamily={FONT_SANS} fontSize={12} opacity={(p - 0.9) / 0.1}>id {id}</text>}
    </g>
  );
};

// ---------- Self-drawing arrow ----------
export const Arrow: React.FC<{
  x1: number; y1: number; x2: number; y2: number; color?: string; progress?: number; width?: number; dashed?: boolean;
}> = ({ x1, y1, x2, y2, color = COLORS.white, progress = 1, width = 2.5, dashed = false }) => {
  const ex = x1 + (x2 - x1) * progress, ey = y1 + (y2 - y1) * progress;
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const ah = 9;
  const a1 = ang - Math.PI / 7, a2 = ang + Math.PI / 7;
  return (
    <g>
      <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={color} strokeWidth={width} strokeLinecap="round"
        strokeDasharray={dashed ? "5 4" : undefined} />
      {progress > 0.9 && (
        <>
          <line x1={ex} y1={ey} x2={ex - ah * Math.cos(a1)} y2={ey - ah * Math.sin(a1)} stroke={color} strokeWidth={width} strokeLinecap="round" />
          <line x1={ex} y1={ey} x2={ex - ah * Math.cos(a2)} y2={ey - ah * Math.sin(a2)} stroke={color} strokeWidth={width} strokeLinecap="round" />
        </>
      )}
    </g>
  );
};

// ---------- Self-drawing rectangle (formula box) ----------
export const DrawRect: React.FC<{
  x: number; y: number; w: number; h: number; progress?: number; color?: string; width?: number;
}> = ({ x, y, w, h, progress = 1, color = COLORS.white, width = 2 }) => (
  <rect x={x} y={y} width={w} height={h} rx={8} fill="none" stroke={color} strokeWidth={width}
    pathLength={1000} strokeDasharray={1000} strokeDashoffset={1000 * (1 - progress)} strokeLinecap="round" />
);

// ---------- Big marker stamp (slams in) ----------
export const Stamp: React.FC<{
  text: string; x: number; y: number; color?: string; rotate?: number; scale?: number; opacity?: number;
}> = ({ text, x, y, color = COLORS.red, rotate = -8, scale = 1, opacity = 1 }) => (
  <g transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale})`} opacity={opacity}>
    <text textAnchor="middle" fill={color} fontFamily="'Permanent Marker', cursive"
      fontSize={62} fontWeight={400} style={{ letterSpacing: 1 }}>{text}</text>
  </g>
);

// ---------- Hand-drawn text reveal (word/letter fade-in like handwriting) ----------
export const HandText: React.FC<{
  x: number; y: number; text: string; color?: string; fontFamily?: string; fontSize?: number; progress?: number;
  anchor?: "start" | "middle" | "end"; fontWeight?: number;
}> = ({ x, y, text, color = COLORS.white, fontFamily = FONT_SANS, fontSize = 16, progress = 1, anchor = "middle", fontWeight = 800 }) => {
  const n = text.length;
  const shown = Math.ceil(n * progress);
  return (
    <text x={x} y={y} textAnchor={anchor} fill={color} fontFamily={fontFamily} fontSize={fontSize} fontWeight={fontWeight}>
      {text.slice(0, shown)}
      {shown < n && <tspan opacity={0.4}>{text.slice(shown, shown + 1)}</tspan>}
    </text>
  );
};

// ============================================================================
// NEW PRIMITIVES for the rebuild
// ============================================================================

// ---------- 12-sided polygon clock ring (per mimo: "it is actually a 12-sided polygon") ----------
// Builds a regular 12-gon with noticeable hand-drawn wobble so it reads as a
// SKETCHY circle (not a geometric polygon). Self-reveals clockwise from the top.
export const Clock12: React.FC<{
  cx: number; cy: number; r: number; progress?: number; color?: string; width?: number; seed?: number;
}> = ({ cx, cy, r, progress = 1, color = COLORS.white, width = 2.5, seed = 7 }) => {
  const sides = 24; // more sides + bigger jitter = reads as a hand-drawn circle
  const pts: string[] = [];
  for (let i = 0; i < sides; i++) {
    const a = (i / sides) * Math.PI * 2 - Math.PI / 2; // start at top
    const rr = r + w(seed, i, 4.5) + w(seed + 3, i, 2.0); // strong hand-drawn wobble on radius
    // also jitter the angle slightly for an organic, imperfect feel
    const aj = a + w(seed + 7, i, 0.02);
    pts.push(`${(cx + rr * Math.cos(aj)).toFixed(2)},${(cy + rr * Math.sin(aj)).toFixed(2)}`);
  }
  const d = "M " + pts.join(" L ") + " Z";
  return <DashDraw d={d} progress={progress} color={color} width={width} />;
};

// ---------- Arc creep: reveal an arc along a circle between two angles ----------
// Used for the consistent-hashing "only this arc moves" highlight.
export const ArcCreep: React.FC<{
  cx: number; cy: number; r: number; fromDeg: number; toDeg: number; progress?: number;
  color?: string; width?: number;
}> = ({ cx, cy, r, fromDeg, toDeg, progress = 1, color = COLORS.white, width = 13 }) => {
  const a0 = (fromDeg - 90) * Math.PI / 180;
  const a1 = (toDeg - 90) * Math.PI / 180;
  const span = toDeg - fromDeg;
  const endDeg = fromDeg + span * progress;
  const ae = (endDeg - 90) * Math.PI / 180;
  const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
  const xe = cx + r * Math.cos(ae), ye = cy + r * Math.sin(ae);
  const large = Math.abs(endDeg - fromDeg) > 180 ? 1 : 0;
  return (
    <path d={`M ${x0} ${y0} A ${r} ${r} 0 ${large} 1 ${xe} ${ye}`}
      fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" opacity={0.7} />
  );
};

// helper: position on clock face from degrees (0=top/12oclock, clockwise)
export function posOnClock(cx: number, cy: number, r: number, deg: number) {
  const a = (deg - 90) * Math.PI / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
}

// ---------- Red-X crossout (two self-drawing diagonals over a target box) ----------
// Used for the %4 -> %5 formula change.
export const RedX: React.FC<{
  cx: number; cy: number; size: number; progress?: number; color?: string;
}> = ({ cx, cy, size, progress = 1, color = COLORS.red }) => {
  const p1 = Math.min(progress * 2, 1);
  const p2 = Math.max(0, Math.min((progress - 0.5) * 2, 1));
  return (
    <g stroke={color} strokeWidth={3} strokeLinecap="round">
      <DrawLine x1={cx - size} y1={cy - size} x2={cx + size} y2={cy + size} progress={p1} color={color} width={3} />
      {p2 > 0 && <DrawLine x1={cx + size} y1={cy - size} x2={cx - size} y2={cy + size} progress={p2} color={color} width={3} />}
    </g>
  );
};
