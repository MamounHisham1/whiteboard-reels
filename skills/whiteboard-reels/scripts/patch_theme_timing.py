#!/usr/bin/env python3
"""Rewrite the `const timing = {...}` block and DURATION_SEC in a video's theme.ts
from the real audio/timing.json. Use this when a scene's theme.ts hardcodes an inline
timing table instead of loading timing.json at build time (some scenes do, for speed).

Format matches [start, end] in seconds, 3 per line.

Usage: patch_theme_timing.py <slug>
Env:   VIDEOS_DIR   default <cwd>/videos
"""
import json, os, re, sys

slug = sys.argv[1] if len(sys.argv) > 1 else None
if not slug:
    print("usage: patch_theme_timing.py <slug>", file=sys.stderr); sys.exit(2)

VIDEOS_DIR = os.environ.get("VIDEOS_DIR", os.path.join(os.getcwd(), "videos"))
BASE = os.path.join(VIDEOS_DIR, slug)
cands = [f"{BASE}/audio/timing.json", f"{BASE}/audio/kokoro/timing.json",
         f"{BASE}/audio/elevenlabs/timing.json"]
tj = next((c for c in cands if os.path.exists(c)), None)
if not tj:
    print(f"ERROR: no timing.json for {slug}", file=sys.stderr); sys.exit(1)
timing = json.load(open(tj))

items, last_end = [], 0.0
for sid, v in timing.items():
    s, e = round(v["start"], 3), round(v["end"], 3)
    items.append(f"{sid}: [{s}, {e}]")
    last_end = e
lines = ["  " + ", ".join(items[i:i+3]) + "," for i in range(0, len(items), 3)]
block = "const timing: Record<string, [number, number]> = {\n" + "\n".join(lines) + "\n};"
duration = round(last_end + 0.8, 2)

theme_path = f"{BASE}/remotion-project/src/theme.ts"
src = open(theme_path).read()
src2 = re.sub(r"const timing[^=]*=\s*\{.*?\};", block, src, count=1, flags=re.DOTALL)
if src2 == src:
    print(f"WARN: timing block not replaced for {slug}", file=sys.stderr)
src3 = re.sub(r"export const DURATION_SEC\s*=\s*[0-9.]+;.*", f"export const DURATION_SEC = {duration};", src2, count=1)
if src3 == src2:
    print(f"WARN: DURATION_SEC not replaced for {slug}", file=sys.stderr)
open(theme_path, "w").write(src3)
print(f"{slug}: {len(timing)} scenes, DURATION_SEC={duration}, last_end={last_end}")
