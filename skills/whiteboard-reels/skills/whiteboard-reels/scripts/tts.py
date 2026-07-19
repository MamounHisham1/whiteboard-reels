#!/usr/bin/env python3
"""Per-scene TTS with ElevenLabs Brian, Kokoro fallback on quota/HTTP error.

Outputs (to videos/<slug>/audio/<engine>/):
  - <scene_id>.mp3 / .wav   per scene
  - timing.json             {scene_id: {start, duration, end}} seconds
  - full_narration.wav/.mp3 concatenated with 0.12s gaps

Usage:
  python3 tts.py <slug>                  # reads videos/<slug>/script.json
  VOICE_USED=<engine> is printed last. Exit 0 on success.

Env:
  ELEVENLABS_API_KEY  required for Brian. If unset or quota exhausted, falls back to Kokoro.
  ELEVEN_VOICE        optional, ElevenLabs voice id (default nPczCjzI2devNBz1zQrb, Brian)
  KOKORO_PYTHON       optional, path to a python interpreter that has `kokoro` installed.
                      No default; must be set if you want the fallback to work.
  KOKORO_VOICE        optional, Kokoro voice name (default am_michael)
  VIDEOS_DIR          optional, root containing per-slug folders (default <cwd>/videos)
"""
import json, os, shutil, subprocess, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _envloader  # noqa: F401  — auto-loads .env if present

SLUG = sys.argv[1] if len(sys.argv) > 1 else None
if not SLUG:
    print("usage: tts.py <slug>", file=sys.stderr); sys.exit(2)

VIDEOS_DIR = os.environ.get("VIDEOS_DIR", os.path.join(os.getcwd(), "videos"))
VIDEO_DIR = os.path.join(VIDEOS_DIR, SLUG)
SCRIPT_PATH = os.path.join(VIDEO_DIR, "script.json")
if not os.path.exists(SCRIPT_PATH):
    print(f"ERROR: {SCRIPT_PATH} not found", file=sys.stderr); sys.exit(1)

# Pre-check ffmpeg/ffprobe (used for every scene); fail loudly instead of cryptic CalledProcessError.
for tool in ("ffmpeg", "ffprobe"):
    if shutil.which(tool) is None:
        print(f"ERROR: {tool} not found on PATH. Install it (apt install ffmpeg / brew install ffmpeg).", file=sys.stderr)
        sys.exit(1)

SCRIPT = json.load(open(SCRIPT_PATH))
VOICE_IN_SCRIPT = SCRIPT.get("voice", "nPczCjzI2devNBz1zQrb")
GAP = 0.12

def dur_seconds(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {r.stderr.strip()}")
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise RuntimeError(f"ffprobe returned no duration for {path} (corrupt wav?)")

def _run(cmd):
    """Run a subprocess, capture stderr, only print it on failure."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\nstderr: {r.stderr.strip()}")
    return r

def write_gap(out_dir):
    gap = os.path.join(out_dir, "_gap.wav")
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i",
          f"anullsrc=channel_layout=mono:sample_rate=44100", "-t", str(GAP), gap])
    return gap

def finalize(out_dir, timing, concat_wavs, voice_used):
    list_path = os.path.join(out_dir, "_concat.txt")
    with open(list_path, "w") as f:
        for w in concat_wavs: f.write(f"file '{w}'\n")
    full_wav = os.path.join(out_dir, "full_narration.wav")
    full_mp3 = os.path.join(out_dir, "full_narration.mp3")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
          "-ar", "44100", "-ac", "1", full_wav])
    _run(["ffmpeg", "-y", "-i", full_wav, "-b:a", "128k", full_mp3])
    json.dump(timing, open(os.path.join(out_dir, "timing.json"), "w"), indent=2)
    # Wire narration into the Remotion project so it just works after TTS.
    public = os.path.join(VIDEO_DIR, "remotion-project", "public")
    if os.path.isdir(public):
        shutil.copy2(full_mp3, os.path.join(public, "narration.mp3"))
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
        _run(["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "1", wav])
        d = dur_seconds(wav)
        timing[sid] = {"start": round(cur, 3), "duration": round(d, 3), "end": round(cur + d, 3)}
        cur += d + GAP; concats += [wav, gap]
    finalize(out_dir, timing, concats, os.environ.get("ELEVEN_VOICE", VOICE_IN_SCRIPT))

# ---- Kokoro fallback (KModel/KPipeline) ----
# KOKORO_PYTHON must point at an interpreter that has the `kokoro` package installed.
# We do NOT hardcode a venv path; the child uses its own sys.path.
KOKORO_RUNNER = os.environ.get("KOKORO_PYTHON")  # no default — must be set
KOKORO_VOICE = os.environ.get("KOKORO_VOICE", "am_michael")
KOKORO_SCRIPT = r'''
import sys
text, out_wav, voice = sys.argv[1], sys.argv[2], sys.argv[3]
from kokoro import KModel, KPipeline
import soundfile as sf
model = KModel().eval()
pipeline = KPipeline(model=model)
audio = pipeline.gen_voice(voice, text, "en-us")
sf.write(out_wav, audio, 24000)
'''
def synth_kokoro(text, out_wav):
    if not KOKORO_RUNNER:
        raise RuntimeError("KOKORO_PYTHON not set (no default — point it at a python with `kokoro` installed)")
    if not os.path.exists(KOKORO_RUNNER):
        raise RuntimeError(f"KOKORO_PYTHON={KOKORO_RUNNER} does not exist")
    _run([KOKORO_RUNNER, "-c", KOKORO_SCRIPT, text, out_wav, KOKORO_VOICE])

def run_kokoro():
    out_dir = os.path.join(VIDEO_DIR, "audio", "kokoro")
    os.makedirs(out_dir, exist_ok=True)
    gap = write_gap(out_dir)
    timing, concats, cur, n = {}, [], 0.0, len(SCRIPT["scenes"])
    for i, sc in enumerate(SCRIPT["scenes"]):
        sid, text = sc["id"], sc["text"]
        print(f"[{i+1}/{n}] {sid} (kokoro {KOKORO_VOICE}): {text[:55]}...", file=sys.stderr)
        wav = os.path.join(out_dir, f"{sid}.wav")
        synth_kokoro(text, wav)
        _run(["ffmpeg", "-y", "-i", wav, "-ar", "44100", "-ac", "1", wav])
        d = dur_seconds(wav)
        timing[sid] = {"start": round(cur, 3), "duration": round(d, 3), "end": round(cur + d, 3)}
        cur += d + GAP; concats += [wav, gap]
    finalize(out_dir, timing, concats, KOKORO_VOICE)

# ---- Dispatch: Brian first, Kokoro on any failure ----
try:
    if not os.environ.get("ELEVENLABS_API_KEY"):
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    run_elevenlabs()
except Exception as e:
    print(f"[tts] ElevenLabs failed ({type(e).__name__}: {e}); falling back to Kokoro {KOKORO_VOICE}.", file=sys.stderr)
    print(f"[tts] NOTE: voice consistency broken if this is mid-batch — flag it.", file=sys.stderr)
    try:
        run_kokoro()
    except Exception as e2:
        print(f"[tts] Kokoro fallback unavailable: {e2}", file=sys.stderr)
        print(f"[tts] To use Kokoro, install one of:", file=sys.stderr)
        print(f"        kokoro (KModel/KPipeline): pip install kokoro soundfile", file=sys.stderr)
        print(f"          then: export KOKORO_PYTHON=<path-to-that-python>", file=sys.stderr)
        print(f"        kokoro_onnx (lighter):     python3 scripts/tts_kokoro_onnx.py <slug>", file=sys.stderr)
        print(f"          (see references/setup.md)", file=sys.stderr)
        print(f"[tts] Or set ELEVENLABS_API_KEY to use Brian.", file=sys.stderr)
        sys.exit(1)
