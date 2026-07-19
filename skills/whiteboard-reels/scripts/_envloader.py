"""Shared .env loader. Import this FIRST in every script that needs env vars.
Loads .env from the project root (cwd) into os.environ if present, without
overwriting vars already set in the real environment.

Usage (at top of any script):
    import _envloader  # noqa: F401  — auto-loads .env if present
"""
import os, sys
from pathlib import Path

def _load_env():
    # walk up from cwd looking for a .env file (max 3 levels)
    for d in [Path.cwd()] + list(Path.cwd().parents)[:3]:
        env_file = d / ".env"
        if env_file.is_file():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"').strip("'")
                if key and key not in os.environ:  # don't clobber real env
                    os.environ[key] = os.path.expanduser(val)  # expand ~/ paths
            return
_load_env()
