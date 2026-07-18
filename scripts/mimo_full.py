#!/usr/bin/env python3
"""Whole-video mimo defect scan. Sends the ENTIRE mp4 as a video_url data URL and asks
mimo to scan the whole thing for text/line/shape defects. No frame-cutting.
Gate = the output contains 'NO DEFECTS FOUND'.

Usage:
  python3 mimo_full.py <video.mp4> [label]

Env: OPENCODE_KEY required.
"""
import base64, json, os, sys, urllib.request, urllib.error

if len(sys.argv) < 2:
    print("usage: mimo_full.py <video.mp4> [label]", file=sys.stderr); sys.exit(2)

VIDEO = sys.argv[1]
LABEL = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(VIDEO)
KEY = os.environ.get("OPENCODE_KEY")
if not KEY:
    print("ERROR: OPENCODE_KEY env var is required.", file=sys.stderr); sys.exit(1)

URL = "https://opencode.ai/zen/go/v1/chat/completions"
MODEL = "mimo-v2.5"

def b64(p):
    with open(p, "rb") as f: return base64.b64encode(f.read()).decode()

PROMPT = (
    "Watch this ENTIRE video carefully from start to finish. It is a vertical (360x640) "
    "hand-drawn whiteboard-style explainer. Your ONLY job is to find VISUAL DEFECTS in text, "
    "lines, and shapes. Do not comment on style/theme/content quality or whether the topic is "
    "interesting — ONLY defects.\n\n"
    "Look for, throughout the WHOLE video (report the approximate timestamp for each):\n"
    "1. TEXT OVERLAP: text overlapping or crossing lines/arrows/shapes/other text so it's hard to read.\n"
    "2. TEXT CLIPPED/CUT: text running off the frame edge or cut by the canvas boundary.\n"
    "3. TEXT ON SHAPES: text drawn on top of a cylinder/box/line so it is illegible.\n"
    "4. SHAPE COLLISIONS: shapes overlapping each other in a way that looks broken (not intentional layering).\n"
    "5. ARROW ISSUES: arrows not reaching their target, overshooting, pointing to empty space, crossing unrelated text, or with detached arrowheads.\n"
    "6. LABEL FIT: labels not fitting inside/under their element or misplaced.\n"
    "7. STACKING/RELAYOUT: elements visibly jumping/moving/resizing when new elements appear (they should stay fixed and accumulate).\n\n"
    "Report EACH defect as a separate item, in this exact format:\n"
    "- [SEVERITY] t=~Ns: (TYPE) specific description of what is wrong and which element/text.\n"
    "  SEVERITY = HIGH (unreadable/broken), MED (ugly but legible), or LOW (minor).\n"
    "  TYPE = one of: text-overlap, text-clipped, text-on-shape, shape-collision, arrow-miss, label-fit, relayout, other.\n\n"
    "If a whole category is clean across the entire video, say 'CLEAN: <category>'. "
    "Be thorough — scan the ENTIRE video, not just the start. If you find nothing, explicitly say "
    "'NO DEFECTS FOUND'. Do not invent problems; only report what you actually see."
)

content = [
    {"type": "text", "text": PROMPT},
    {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64(VIDEO)}"}},
]
payload = {"model": MODEL, "messages": [{"role": "user", "content": content}], "temperature": 0.2}
req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
             "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) opencode-cli/1.0 whiteboard-reels"},
    method="POST")

print(f"[mimo_full] label={LABEL}", file=sys.stderr)
print(f"[mimo_full] {VIDEO}", file=sys.stderr)
print(f"[mimo_full] sending WHOLE mp4 to mimo-v2.5 (never frames)...", file=sys.stderr)
try:
    with urllib.request.urlopen(req, timeout=900) as resp:
        data = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:400]}", file=sys.stderr); sys.exit(1)
except urllib.error.URLError as e:
    print(f"URL error (mimo hung/unreachable): {e}", file=sys.stderr); sys.exit(1)

out = data["choices"][0]["message"].get("content") or "(no content)"
print(f"===== {LABEL} =====")
print(out)
clean = "NO DEFECTS FOUND" in out.upper()
print(f"\n[mimo_full] usage: {json.dumps(data.get('usage', {}))}", file=sys.stderr)
print(f"[mimo_full] GATE: {'PASS' if clean else 'FAIL'}", file=sys.stderr)
sys.exit(0 if clean else 1)
