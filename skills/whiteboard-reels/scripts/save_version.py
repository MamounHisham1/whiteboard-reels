#!/usr/bin/env python3
"""Save the latest render as a versioned copy. Never overwrites.
Copies videos/<slug>/remotion-project/out/video.mp4 -> versions/video_v<N+1>.mp4

Usage:
  python3 save_version.py <slug_or_path>
  python3 save_version.py videos/bloom-filters
  python3 save_version.py videos/bloom-filters/remotion-project
"""
import os, sys, re, shutil

arg = sys.argv[1] if len(sys.argv) > 1 else None
if not arg:
    print("usage: save_version.py <slug_or_path>", file=sys.stderr); sys.exit(2)

# resolve arg to a remotion-project dir
proj = arg
if not os.path.basename(proj).startswith("remotion"):
    proj = os.path.join(arg, "remotion-project") if os.path.isdir(arg) else os.path.join("videos", arg, "remotion-project")
proj = proj.rstrip("/")

src = os.path.join(proj, "out", "video.mp4")
versions = os.path.join(proj, "versions")
if not os.path.exists(src):
    print(f"ERROR: {src} not found (render first).", file=sys.stderr); sys.exit(1)
os.makedirs(versions, exist_ok=True)

existing = [f for f in os.listdir(versions) if re.fullmatch(r"video_v\d+\.mp4", f)]
next_n = max([int(re.search(r"\d+", f).group()) for f in existing], default=0) + 1
dst = os.path.join(versions, f"video_v{next_n}.mp4")
shutil.copy2(src, dst)

print(f"[save_version] {os.path.basename(os.path.dirname(proj))} -> versions/video_v{next_n}.mp4")
print(f"[save_version] {dst}")
print(f"VERSION=v{next_n}")
