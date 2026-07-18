#!/usr/bin/env python3
"""Per-scene TTS with ElevenLabs Brian, Kokoro fallback on quota/HTTP error.
Mirrors the original tts_elevenlabs.py timing schema.

Outputs (to videos/<slug>/audio/<engine>/):
  - <scene_id>.mp3 / .wav   per scene
  - timing.json             {scene_id: {start, duration, end}} seconds
  - full_narration.wav/.mp3 concatenated with 0.12s gaps

Usage:
  python3 tts.py <slug>                  # reads videos/<slug>/script.json
  VOICE_USED=<engine> is printed last. Exit 0 on success.

Env:
  ELEVENLABS_API_KEY  required for Brian. If unset or quota exhausted, falls back to Kokoro.
  ELEVEN_VOICE        optional, default nPczCjzI2devNBz1zQrb (Brian)
  KOKORO_PYTHON       optional, default /tmp/kokoro-env/bin/python3
"""
import json, os, subprocess, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _envloader  # noqa: F401  — auto-loads .env if present

SLUG = sys.argv[1] if len(sys.argv) > 1 else None
if not SLUG:
    print("usage: tts.py <slug>", file=sys.stderr); sys.exit(2)

BASE = os.getcwd()
VIDEO_DIR = os.path.join(BASE, "videos", SLUG)
SCRIPT_PATH = os.path.join(VIDEO_DIR, "script.json")
if not os.path.exists(SCRIPT_PATH):
    print(f"ERROR: {SCRIPT_PATH} not found", file=sys.stderr); sys.exit(1)

SCRIPT = json.load(open(SCRIPT_PATH))
VOICE_IN_SCRIPT = SCRIPT.get("voice", "nPczCjzI2devNBz1zQrb")
GAP = 0.12

def dur_seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out)

def write_gap(out_dir):
    gap = os.path.join(out_dir, "_gap.wav")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"anullsrc=channel_layout=mono:sample_rate=44100", "-t", str(GAP), gap],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return gap

def finalize(out_dir, timing, concat_wavs, voice_used):
    list_path = os.path.join(out_dir, "_concat.txt")
    with open(list_path, "w") as f:
        for w in concat_wavs: f.write(f"file '{w}'\n")
    full_wav = os.path.join(out_dir, "full_narration.wav")
    full_mp3 = os.path.join(out_dir, "full_narration.mp3")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                    "-ar", "44100", "-ac", "1", full_wav],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-i", full_wav, "-b:a", "128k", full_mp3],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    json.dump(timing, open(os.path.join(out_dir, "timing.json"), "w"), indent=2)
    total = sum(s["duration"] + GAP for s in timing.values())
    print(f"\n[tts] voice_used={voice_used} scenes={len(timing)} total={total:.2f}s", file=sys.stderr)
    print(f"[tts] timing -> {out_dir}/timing.json", file=sys.stderr)
    print(f"VOICE_USED={voice_used}")
    print(f"TOTAL_DURATION={total:.3f}")

# ---- ElevenLabs Brian ----
def synth_elevenlabs(text, out_mp3):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key: raise RuntimeError("no ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVEN_VOICE", VOICE_IN_SCRIPT)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    payload = {"text": text, "model_id": "eleven_multilingual_v2",
               "voice_settings": {"stability": 0.50, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(out_mp3, "wb") as f: f.write(resp.read())

def run_elevenlabs():
    out_dir = os.path.join(VIDEO_DIR, "audio", "elevenlabs")
    os.makedirs(out_dir, exist_ok=True)
    gap = write_gap(out_dir)
    timing, concats, cur, n = {}, [], 0.0, len(SCRIPT["scenes"])
    for i, sc in enumerate(SCRIPT["scenes"]):
        sid, text = sc["id"], sc["text"]
        print(f"[{i+1}/{n}] {sid}: {text[:55]}...", file=sys.stderr)
        mp3 = os.path.join(out_dir, f"{sid}.mp3"); wav = os.path.join(out_dir, f"{sid}.wav")
        synth_elevenlabs(text, mp3)
        subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", wav],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        d = dur_seconds(wav)
        timing[sid] = {"start": round(cur, 3), "duration": round(d, 3), "end": round(cur + d, 3)}
        cur += d + GAP; concats += [wav, gap]
    finalize(out_dir, timing, concats, os.environ.get("ELEVEN_VOICE", VOICE_IN_SCRIPT))

# ---- Kokoro am_michael fallback ----
KOKORO_RUNNER = os.environ.get("KOKORO_PYTHON", "/tmp/kokoro-env/bin/python3")
KOKORO_SCRIPT = r'''
import sys, json, subprocess, os
text, out_wav = sys.argv[1], sys.argv[2]
sys.path.insert(0, "/tmp/kokoro-env/lib/python3.11/site-packages")
from kokoro import KModel, KPipeline
import soundfile as sf
model = KModel().eval()
pipeline = KPipeline(model=model)
audio = pipeline.gen_voice("am_michael", text, "en-us")
sf.write(out_wav, audio, 24000)
'''
def synth_kokoro(text, out_wav):
    runner = KOKORO_RUNNER if os.path.exists(KOKORO_RUNNER) else "python3"
    subprocess.run([runner, "-c", KOKORO_SCRIPT, text, out_wav], check=True)

def run_kokoro():
    out_dir = os.path.join(VIDEO_DIR, "audio", "kokoro")
    os.makedirs(out_dir, exist_ok=True)
    gap = write_gap(out_dir)
    timing, concats, cur, n = {}, [], 0.0, len(SCRIPT["scenes"])
    for i, sc in enumerate(SCRIPT["scenes"]):
        sid, text = sc["id"], sc["text"]
        print(f"[{i+1}/{n}] {sid} (kokoro): {text[:55]}...", file=sys.stderr)
        wav = os.path.join(out_dir, f"{sid}.wav")
        synth_kokoro(text, wav)
        subprocess.run(["ffmpeg", "-y", "-i", wav, "-ar", "44100", "-ac", "1", wav],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        d = dur_seconds(wav)
        timing[sid] = {"start": round(cur, 3), "duration": round(d, 3), "end": round(cur + d, 3)}
        cur += d + GAP; concats += [wav, gap]
    finalize(out_dir, timing, concats, "am_michael")

# ---- Dispatch: Brian first, Kokoro on any failure ----
try:
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    run_elevenlabs()
except Exception as e:
    print(f"[tts] ElevenLabs failed ({type(e).__name__}: {e}); falling back to Kokoro am_michael.", file=sys.stderr)
    print(f"[tts] NOTE: voice consistency broken — flag this to the user.", file=sys.stderr)
    try:
        run_kokoro()
    except Exception as e2:
        print(f"[tts] Kokoro also failed: {e2}", file=sys.stderr); sys.exit(1)
