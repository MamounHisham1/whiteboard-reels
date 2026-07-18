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

The reference narrator is the "Brian" voice (id `nPczCjzI2devNBz1zQrb`). 10k chars/month is
enough for roughly 5-7 videos before you hit the wall. When you hit it, either wait for the
monthly reset, upgrade, or use the Kokoro fallback (below).

## Optional: ELEVEN_VOICE

Override the voice id if you want a different narrator. Default is Brian:
```bash
export ELEVEN_VOICE=nPczCjzI2devNBz1zQrb
```

## Optional: Kokoro fallback (KOKORO_PYTHON)

If ElevenLabs is unavailable or quota-exhausted, `tts.py` falls back to Kokoro (`am_michael`
voice). **Kokoro is not bundled** — it only works if you've installed it locally:

```bash
python -m venv /tmp/kokoro-env
/tmp/kokoro-env/bin/pip install kokoro soundfile
export KOKORO_PYTHON=/tmp/kokoro-env/bin/python3
```

Caveat: Kokoro's `am_michael` sounds different from Brian, so using it **breaks voice
consistency** across your series. The skill prints a loud warning when this happens. For a
consistent series, keep ElevenLabs Brian as the primary voice.

## Using a .env file

If you prefer not to export vars in every shell, copy `.env.example` to `.env` in your project
root and fill in your keys. Then source it before running the pipeline:

```bash
cp skills/whiteboard-reels/.env.example .env
# edit .env with your keys
set -a; source .env; set +a
```

## Verify it's all set

```bash
python3 scripts/check_env.py
# expect: OPENCODE_KEY: set, ELEVENLABS_API_KEY: set, tools: ok
```
