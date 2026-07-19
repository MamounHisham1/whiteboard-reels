#!/usr/bin/env python3
"""Scaffold a new whiteboard-reels video folder.

Creates:
  videos/<slug>/
  ├── script.json          (template, edit the scenes for your topic)
  └── remotion-project/    (seeded from assets/ — Primitives, theme, package.json)

Usage:
  python3 scaffold.py <slug> [--headline "BLOOM FILTERS"]

The remotion-project src/ scenes are intentionally NOT scaffolded — you write ORIGINAL
Chapter1/TitleCard/Chapter2 per topic. Only the shared shell (Primitives, theme, fonts,
deps, index/Root wiring) is copied.

This script is path-portable: it finds the skill root by walking up from its own location
until it finds assets/Primitives.tsx.
"""
import os, sys, shutil, json

def skill_root():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(d, "assets", "Primitives.tsx")): return d
        d = os.path.dirname(d)
    print("ERROR: could not locate skill root (assets/Primitives.tsx).", file=sys.stderr); sys.exit(1)

ROOT = os.environ.get("VIDEOS_DIR", os.getcwd())
SLUG = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
if not SLUG:
    print('usage: scaffold.py <slug> [--headline "TOPIC NAME"]', file=sys.stderr); sys.exit(2)

HEADLINE = "TOPIC NAME"
if "--headline" in sys.argv:
    HEADLINE = sys.argv[sys.argv.index("--headline") + 1]

SKILL = skill_root()
VIDEO_DIR = os.path.join(ROOT, "videos", SLUG) if os.path.basename(ROOT) != "videos" else os.path.join(ROOT, SLUG)
PROJ_DIR = os.path.join(VIDEO_DIR, "remotion-project")

if os.path.exists(VIDEO_DIR):
    print(f"ERROR: {VIDEO_DIR} already exists.", file=sys.stderr); sys.exit(1)
os.makedirs(PROJ_DIR, exist_ok=True)

# 1. script.json template
headline_slug = HEADLINE.upper()
script = {
    "title": "SYSTEM DESIGN",
    "headline": headline_slug,
    "voice": "nPczCjzI2devNBz1zQrb",
    "scenes": [{"id": f"s{i}", "text": f"<scene {i} narration beat>"} for i in range(1, 18)],
}
json.dump(script, open(os.path.join(VIDEO_DIR, "script.json"), "w"), indent=2)

# 2. seed remotion-project from assets/.
# Copy the TS source files into src/, but package.json goes to the project root (NOT src/).
src_dir = os.path.join(PROJ_DIR, "src")
os.makedirs(src_dir, exist_ok=True)
for name in os.listdir(os.path.join(SKILL, "assets")):
    if name == "package.json": continue  # handled below, goes to project root
    shutil.copy(os.path.join(SKILL, "assets", name), os.path.join(src_dir, name))
shutil.copy(os.path.join(SKILL, "assets", "package.json"), os.path.join(PROJ_DIR, "package.json"))
os.makedirs(os.path.join(PROJ_DIR, "public"), exist_ok=True)
os.makedirs(os.path.join(PROJ_DIR, "out"), exist_ok=True)
os.makedirs(os.path.join(PROJ_DIR, "versions"), exist_ok=True)
os.makedirs(os.path.join(PROJ_DIR, "reels"), exist_ok=True)
os.makedirs(os.path.join(src_dir, "scenes"), exist_ok=True)  # referenced by next-step hint

print(f"[scaffold] created {VIDEO_DIR}")
print(f"[scaffold] edit videos/{SLUG}/script.json  (write your ~15-18 scene beats)")
print(f"[scaffold] write videos/{SLUG}/remotion-project/src/scenes/  (ORIGINAL diagrams for this topic)")
print(f"[scaffold] then: python3 scripts/tts.py {SLUG}")
print(f"[scaffold] then: cd videos/{SLUG}/remotion-project && npm install && npx remotion render <Comp> out/video.mp4")
