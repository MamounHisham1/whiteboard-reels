#!/usr/bin/env python3
"""Kokoro (kokoro_onnx) per-scene TTS — the fallback that actually works on this box.

Unlike tts.py's `from kokoro import KModel, KPipeline` path, this uses the lighter
`kokoro_onnx` package with the int8 ONNX model. Use this when ElevenLabs quota is gone
for a whole batch and you want a consistent local voice across the series.

Writes videos/<slug>/audio/{<sid>.wav, timing.json, full_narration.wav+mp3} FLAT
(no engine subdir) and copies full_narration.mp3 -> remotion-project/public/narration.mp3.
theme.ts loadTiming() looks in audio/timing.json first, so this wiring is zero-config.

Usage: tts_kokoro_onnx.py <slug> [speed]     # default speed 1.05

Env (override the defaults if your model lives elsewhere):
  KOKORO_ONNX_MODEL   default /tmp/kokoro-env/kokoro-v1.0.int8.onnx
  KOKORO_ONNX_VOICES  default /tmp/kokoro-env/voices-v1.0.bin
  KOKORO_ONNX_VOICE   default am_michael
  VIDEOS_DIR          default <cwd>/videos
"""
import json, os, sys, subprocess, shutil
import numpy as np
from kokoro_onnx import Kokoro
import soundfile as sf

slug = sys.argv[1] if len(sys.argv) > 1 else None
if not slug:
    print("usage: tts_kokoro_onnx.py <slug> [speed]", file=sys.stderr); sys.exit(2)
speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.05

VIDEOS_DIR = os.environ.get("VIDEOS_DIR", os.path.join(os.getcwd(), "videos"))
BASE = os.path.join(VIDEOS_DIR, slug)
SCRIPT = json.load(open(os.path.join(BASE, "script.json")))
OUT = os.path.join(BASE, "audio")
os.makedirs(OUT, exist_ok=True)

MODEL = os.environ.get("KOKORO_ONNX_MODEL", "/tmp/kokoro-env/kokoro-v1.0.int8.onnx")
VOICES = os.environ.get("KOKORO_ONNX_VOICES", "/tmp/kokoro-env/voices-v1.0.bin")
VOICE = os.environ.get("KOKORO_ONNX_VOICE", "am_michael")
GAP = 0.12

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
subprocess.run(["ffmpeg", "-y", "-i", os.path.join(OUT, "full_narration.wav"), "-b:a", "128k",
                os.path.join(OUT, "full_narration.mp3")],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
json.dump(timing, open(os.path.join(OUT, "timing.json"), "w"), indent=2)

pub = os.path.join(BASE, "remotion-project", "public")
os.makedirs(pub, exist_ok=True)
shutil.copy2(os.path.join(OUT, "full_narration.mp3"), os.path.join(pub, "narration.mp3"))

print(f"\n{slug}: total {cur:.2f}s ({len(SCRIPT['scenes'])} scenes)", file=sys.stderr)
print(f"VOICE_USED={VOICE}")
print(f"FULL_DURATION={cur:.3f}")
