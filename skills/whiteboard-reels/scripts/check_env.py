#!/usr/bin/env python3
"""Check that required env vars and tools are set. Run this FIRST before any build.
Prints a clear report: which keys are set/missing, where to get them, and whether
the required tools (node, remotion, python3, ffmpeg) are on PATH.

Usage:
  python3 scripts/check_env.py
Exit 0 if required vars set, 1 if any required var missing.
"""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _envloader  # noqa: F401  — auto-loads .env if present

REQUIRED = [
    ("OPENCODE_KEY",    "mimo-v2.5 verification gate", "https://opencode.ai/zen"),
    ("ELEVENLABS_API_KEY", "Brian voice TTS",          "https://elevenlabs.io"),
]
OPTIONAL = [
    ("ELEVEN_VOICE",    "voice id (default Brian nPczCjzI2devNBz1zQrb)"),
    ("KOKORO_PYTHON",   "kokoro fallback python (default /tmp/kokoro-env/bin/python3)"),
]
TOOLS = ["node", "npx", "python3", "ffmpeg", "ffprobe"]

def mask(v): return v[:6] + "..." + v[-4:] if v and len(v) > 12 else (v or "(empty)")

print("=== whiteboard-reels environment check ===\n")

missing = []
print("REQUIRED env vars:")
for name, why, url in REQUIRED:
    val = os.environ.get(name)
    if val:
        print(f"  [SET]   {name} = {mask(val)}  ({why})")
    else:
        print(f"  [MISS]  {name}  ({why})")
        print(f"          get it: {url}")
        print(f"          set:    export {name}=<your-key>")
        missing.append(name)

print("\nOPTIONAL env vars:")
for name, why in OPTIONAL:
    val = os.environ.get(name)
    print(f"  [{'SET ' if val else 'def'}]   {name} = {mask(val) if val else why}")

print("\nTOOLS on PATH:")
for t in TOOLS:
    ok = shutil.which(t) is not None
    print(f"  [{'ok ' if ok else 'MISS'}]   {t}")

print()
if missing:
    print(f"MISSING required vars: {', '.join(missing)}")
    print("Fix: see references/setup.md, or copy .env.example -> .env and source it.")
    print("  set -a; source .env; set +a")
    sys.exit(1)
print("All required vars set. Ready to build.")
sys.exit(0)
