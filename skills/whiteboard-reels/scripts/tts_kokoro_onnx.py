#!/usr/bin/env python3
"""Kokoro (kokoro_onnx) per-scene TTS — lighter fallback path using the int8 ONNX model.

Use this when ElevenLabs is unavailable and you have `kokoro_onnx` installed locally
(it's lighter than the full `kokoro` KModel/KPipeline package). Keep a whole batch on
the same fallback voice for consistency.

Writes videos/<slug>/audio/{<sid>.wav, timing.json, full_narration.wav+mp3} FLAT
(no engine subdir) and copies full_narration.mp3 -> remotion-project/public/narration.mp3.
theme.ts loadTiming() looks in audio/timing.json first, so this wiring is zero-config.

Usage: tts_kokoro_onnx.py <slug> [speed]     # default speed 1.05

Env (all required for this script to run — NO defaults, you must point at your files):
  KOKORO_ONNX_MODEL   path to kokoro-v1.0.int8.onnx (or equivalent)
  KOKORO_ONNX_VOICES  path to voices-v1.0.bin (or equivalent)
  KOKORO_ONNX_VOICE   optional, voice name (default am_michael)
  VIDEOS_DIR          optional, root containing per-slug folders (default <cwd>/videos)

Install:
  pip install kokoro-onnx soundfile numpy
  Download the model + voices files (see references/setup.md), then export their paths.
"""
import json, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _envloader  # noqa: F401  — auto-loads .env if present

# Guard optional deps — fail with install instructions instead of a raw traceback.
try:
    import numpy as np
    from kokoro_onnx import Kokoro
    import soundfile as sf
except ImportError as e:
    print(f"ERROR: missing dependency for kokoro_onnx TTS: {e}", file=sys.stderr)
    print("Install with:  pip install kokoro-onnx soundfile numpy", file=sys.stderr)
    print("Then set KOKORO_ONNX_MODEL and KOKORO_ONNX_VOICES to your model/voices files.", file=sys.stderr)
    print("See references/setup.md.", file=sys.stderr)
    sys.exit(1)

slug = sys.argv[1] if len(sys.argv) > 1 else None
if not slug:
    print("usage: tts_kokoro_onnx.py <slug> [speed]", file=sys.stderr); sys.exit(2)
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.05

VIDEOS_DIR = os.environ.get("VIDEOS_DIR", os.path.join(os.getcwd(), "videos"))
BASE = os.path.join(VIDEOS_DIR, slug)
script_path = os.path.join(BASE, "script.json")
if not os.path.exists(script_path):
    print(f"ERROR: {script_path} not found", file=sys.stderr); sys.exit(1)
SCRIPT = json.load(open(script_path))
OUT = os.path.join(BASE, "audio")
os.makedirs(OUT, exist_ok=True)

MODEL = os.environ.get("KOKORO_ONNX_MODEL")
VOICES = os.environ.get("KOKORO_ONNX_VOICES")
VOICE = os.environ.get("KOKORO_ONNX_VOICE", "am_michael")
GAP = 0.12

# No defaults — both paths are required. Fail clearly.
missing = [n for n, v in [("KOKORO_ONNX_MODEL", MODEL), ("KOKORO_ONNX_VOICES", VOICES)] if not v]
if missing:
    print(f"ERROR: {', '.join(missing)} env var(s) not set.", file=sys.stderr)
    print("This script has NO default model path — point at your downloaded files.", file=sys.stderr)
    print("  export KOKORO_ONNX_MODEL=/path/to/kokoro-v1.0.int8.onnx", file=sys.stderr)
    print("  export KOKORO_ONNX_VOICES=/path/to/voices-v1.0.bin", file=sys.stderr)
    print("See references/setup.md for where to get the files.", file=sys.stderr)
    sys.exit(1)
for label, p in [("KOKORO_ONNX_MODEL", MODEL), ("KOKORO_ONNX_VOICES", VOICES)]:
    if not os.path.exists(p):
        print(f"ERROR: {label}={p} does not exist.", file=sys.stderr); sys.exit(1)

# Pre-check ffmpeg.
if shutil.which("ffmpeg") is None:
    print("ERROR: ffmpeg not found on PATH. Install it (apt install ffmpeg / brew install ffmpeg).", file=sys.stderr)
    sys.exit(1)

print(f"Loading Kokoro (onnx) for {slug}: voice={VOICE} speed={speed}", file=sys.stderr)
k = Kokoro(MODEL, VOICES)

timing, all_samples, cur, sr = {}, [], 0.0, 24000
for i, scene in enumerate(SCRIPT["scenes"]):
    sid, text = scene["id"], scene["text"]
    print(f"[{i+1}/{len(SCRIPT['scenes'])}] {sid}: {text[:50]}...", file=sys.stderr)
    samples, sr = k.create(text, voice=VOICE, speed=speed)
    sf.write(os.path.join(OUT, f"{sid}.wav"), samples, sr)
    dur = len(samples) / sr
    timing[sid] = {"start": round(cur, 3), "duration": round(dur, 3), "end": round(cur + dur, 3)}
    cur += dur
    all_samples.append(samples); all_samples.append(np.zeros(int(GAP * sr), dtype=np.float32))
    cur += GAP

full = np.concatenate(all_samples)
sf.write(os.path.join(OUT, "full_narration.wav"), full, sr)
r = subprocess.run(["ffmpeg", "-y", "-i", os.path.join(OUT, "full_narration.wav"), "-b:a", "128k",
                    os.path.join(OUT, "full_narration.mp3")], capture_output=True, text=True)
if r.returncode != 0:
    print(f"ERROR: ffmpeg mp3 encode failed: {r.stderr.strip()}", file=sys.stderr); sys.exit(1)
json.dump(timing, open(os.path.join(OUT, "timing.json"), "w"), indent=2)

pub = os.path.join(BASE, "remotion-project", "public")
os.makedirs(pub, exist_ok=True)
shutil.copy2(os.path.join(OUT, "full_narration.mp3"), os.path.join(pub, "narration.mp3"))

print(f"\n{slug}: total {cur:.2f}s ({len(SCRIPT['scenes'])} scenes)", file=sys.stderr)
print(f"VOICE_USED={VOICE}")
print(f"FULL_DURATION={cur:.3f}")
