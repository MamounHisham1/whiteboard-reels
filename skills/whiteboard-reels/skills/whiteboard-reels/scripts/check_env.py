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
    ("ELEVEN_VOICE",        "ElevenLabs voice id (default nPczCjzI2devNBz1zQrb, Brian)"),
    ("KOKORO_PYTHON",       "path to a python with `kokoro` installed (no default)"),
    ("KOKORO_VOICE",        "Kokoro voice name (default am_michael)"),
    ("KOKORO_ONNX_MODEL",   "path to kokoro-v1.0.int8.onnx (no default)"),
    ("KOKORO_ONNX_VOICES",  "path to voices-v1.0.bin (no default)"),
    ("KOKORO_ONNX_VOICE",   "kokoro_onnx voice name (default am_michael)"),
    ("VIDEOS_DIR",          "root containing per-slug folders (default <cwd>/videos)"),
]
TOOLS = ["node", "npx", "python3", "ffmpeg", "ffprobe"]

# Values that are obviously still the placeholder from .env.example.
def PLACEHOLDERish(v):
    if v is None: return False
    return (
        set(v.strip()) <= set("xX-")                       # sk-xxxx... / sk_xxx...
        or v.strip().startswith("sk-xxx") or v.strip().startswith("sk_xxx")
        or "your-key" in v.lower() or "your-token" in v.lower() or "put-your" in v.lower()
    )

def mask(v): return v[:6] + "..." + v[-4:] if v and len(v) > 12 else (v or "(empty)")

print("=== whiteboard-reels environment check ===\n")

missing, placeholder = [], []
print("REQUIRED env vars:")
for name, why, url in REQUIRED:
    val = os.environ.get(name)
    if val and not PLACEHOLDERish(val):
        print(f"  [SET]   {name} = {mask(val)}  ({why})")
    elif val and PLACEHOLDERish(val):
        print(f"  [PLACEHOLDER] {name} = {mask(val)}  (still the .env.example placeholder)")
        print(f"          get it: {url}")
        print(f"          set:    export {name}=<your-real-key>")
        placeholder.append(name)
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
problems = missing + placeholder
if problems:
    if missing:    print(f"MISSING required vars: {', '.join(missing)}")
    if placeholder: print(f"PLACEHOLDER values (not real keys): {', '.join(placeholder)}")
    print("Fix: see references/setup.md, or copy .env.example -> .env and edit in your real keys.")
    print("  set -a; source .env; set +a")
    sys.exit(1)
print("All required vars set. Ready to build.")
sys.exit(0)
