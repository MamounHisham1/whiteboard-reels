# Setup — get your keys before you build

This skill ships with **no hardcoded secrets**. You must provide two API keys as environment
variables. The build will not work without them.

## Quick check

Run this first. It tells you which keys are set and which are missing:

```bash
python3 scripts/check_env.py
```

## 1. OPENCODE_KEY (required — the mimo verification gate)

This is the bearer token for mimo-v2.5 via opencode zen. **Without it, no verification runs**
and the skill will refuse to proceed at the verify step.

- Where to get it: https://opencode.ai/zen (sign in, generate an API token)
- Format: `sk-...` (long string)
- Set it:
  ```bash
  export OPENCODE_KEY=sk-your-token-here
  ```
- Persist it (so it survives new shells) — add the same line to `~/.bashrc` or `~/.zshrc`.

## 2. ELEVENLABS_API_KEY (required for Brian voice)

- Where to get it: https://elevenlabs.io (sign up, free tier = 10,000 characters/month)
- Format: `sk_...`
- Set it:
  ```bash
  export ELEVENLABS_API_KEY=sk_your-key-here
  ```

The default narrator is the "Brian" voice (id `nPczCjzI2devNBz1zQrb`), a public preset voice.
10k chars/month covers roughly a handful of ~3-minute videos; your mileage depends on script
length. When you hit the wall, either wait for the monthly reset, upgrade, or use the Kokoro
fallback (below).

**Voice access is per-account.** `nPczCjzI2devNBz1zQrb` is widely accessible, but if `tts.py`
returns a voice-access error, either add the voice to your account from the ElevenLabs Voice
Library, or set `ELEVEN_VOICE` to any voice id listed in your own account.

## Optional: ELEVEN_VOICE

Override the ElevenLabs voice id if you want a different narrator. Default is Brian:
```bash
export ELEVEN_VOICE=nPczCjzI2devNBz1zQrb
```

## Optional: Kokoro fallback (local, no API key)

If ElevenLabs is unavailable or quota-exhausted, fall back to Kokoro (`am_michael` voice).
**Kokoro is not bundled** — install it locally. There are two Kokoro paths; use whichever
matches what you install.

Pick a **persistent** directory (not `/tmp` — it's wiped on reboot on most Linux distros).
The examples below use `~/.local/kokoro`, but any persistent path works.

**Option A — `kokoro_onnx` (lighter, int8 ONNX model):** driven by
`scripts/tts_kokoro_onnx.py`. Writes `audio/` flat and wires `public/narration.mp3` automatically.
```bash
python -m venv ~/.local/kokoro
~/.local/kokoro/bin/pip install kokoro-onnx soundfile numpy
# Download the model + voices files into ~/.local/kokoro/ (or anywhere persistent):
#   kokoro-v1.0.int8.onnx   and   voices-v1.0.bin
# Then point the env vars at them:
export KOKORO_ONNX_MODEL=~/.local/kokoro/kokoro-v1.0.int8.onnx
export KOKORO_ONNX_VOICES=~/.local/kokoro/voices-v1.0.bin
python3 scripts/tts_kokoro_onnx.py <slug>
```

**Option B — `kokoro` (KModel/KPipeline):** driven by `tts.py`'s built-in fallback, gated by
`KOKORO_PYTHON`.
```bash
~/.local/kokoro/bin/pip install kokoro soundfile
export KOKORO_PYTHON=~/.local/kokoro/bin/python3
```

Caveats:
- Kokoro's `am_michael` sounds different from Brian, so using it **breaks voice consistency**
  vs. earlier Brian videos. The tools flag it loudly when the fallback runs.
- **When quota is gone for a whole batch, keep the ENTIRE batch on the same fallback voice**
  (`am_michael`) so at least that batch is internally consistent. Do not mix Brian and Kokoro
  within one run.

## Using a .env file

If you prefer not to export vars in every shell, copy `.env.example` to `.env` in your project
root and fill in your keys. The scripts auto-load `.env` if present (real env vars take
precedence). `~` in values is expanded to your home dir.

```bash
cp skills/whiteboard-reels/.env.example .env
# edit .env with your keys
set -a; source .env; set +a    # optional — scripts auto-load .env anyway
```

## Verify it's all set

```bash
python3 scripts/check_env.py
# expect: OPENCODE_KEY: set, ELEVENLABS_API_KEY: set, tools: ok
```
