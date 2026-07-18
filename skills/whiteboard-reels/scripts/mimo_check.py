#!/usr/bin/env python3
"""Single-focus mimo check. Sends the WHOLE video to mimo with ONE constrained question.
Reliable per-issue signal (unlike the free-form whole-video rubric).

Usage:
  python3 mimo_check.py <video.mp4> <focus>
  <focus> in: persistent-canvas | self-drawing | vertical-fill |
            arrow-targeting | text-legibility | theme-match

Env: OPENCODE_KEY required (bearer token for opencode zen).
"""
import base64, json, os, sys, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _envloader  # noqa: F401  — auto-loads .env if present

FOCUSES = {
    "persistent-canvas": (
        "Watch this whole video. It is a vertical hand-drawn whiteboard explainer. "
        "Focus ONLY on this question: when a NEW element is added to a set (e.g. a 4th or 5th "
        "cylinder/shard/node), do the EXISTING elements stay at their fixed positions and sizes, "
        "or do they visibly JUMP, MOVE, or RESIZE to make room? Persistent canvas = they stay put; "
        "relayout = they shift. Look at every moment a new element appears, across the whole video.\n\n"
        "Final line must be exactly: VERDICT: PERSISTENT  or  VERDICT: RELAYOUT\n"
        "If RELAYOUT, on the line before give: DETAIL: <which moment(s), in seconds, what moved>"
    ),
    "self-drawing": (
        "Watch this whole video. Focus ONLY on this: do the strokes appear PROGRESSIVELY (as if a "
        "pen is drawing them in, via stroke-dashoffset), or do shapes/text POP IN fully-formed with "
        "no drawing animation? Look across the whole video.\n\n"
        "Final line must be exactly: VERDICT: SELF_DRAWING  or  VERDICT: POPS_IN\n"
        "If POPS_IN, on the line before give: DETAIL: <which elements at what times>"
    ),
    "vertical-fill": (
        "Watch this whole video. It is 360x640 portrait. Focus ONLY on layout: is the TOP THIRD of "
        "the frame used by content (text, shapes, headers), or is it mostly EMPTY BLACK while all "
        "content stacks in the middle/bottom? This 'stacking at the bottom' is a known defect.\n\n"
        "Final line must be exactly: VERDICT: TOP_USED  or  VERDICT: TOP_EMPTY\n"
        "If TOP_EMPTY, on the line before give: DETAIL: <approx % of top that is empty, and when>"
    ),
    "arrow-targeting": (
        "Watch this whole video. Focus ONLY on arrows: do arrow tips actually LAND ON their target "
        "shapes (touching the cylinder/box/node they point at), or do they STOP IN EMPTY SPACE "
        "above/beside the target, overshoot, or have detached arrowheads? Check every arrow.\n\n"
        "Final line must be exactly: VERDICT: LANDS_ON  or  VERDICT: STOPS_IN_SPACE\n"
        "If STOPS_IN_SPACE, on the line before give: DETAIL: <which arrows at what times>"
    ),
    "text-legibility": (
        "Watch this whole video. Focus ONLY on text: is any text (titles, labels, formula, stamps, "
        "captions) OVERLAPPING lines/shapes/other text, CLIPPED at the frame edge, drawn ON TOP of "
        "a shape so it's illegible, or otherwise unreadable?\n\n"
        "Final line must be exactly: VERDICT: CLEAN  or  VERDICT: DEFECT\n"
        "If DEFECT, list each issue on its own line: DETAIL: [t=~Ns] <what text, what's wrong>"
    ),
    "theme-match": (
        "Watch this whole video. It should match a reference 'digital whiteboard / scribe' style: "
        "pure BLACK background, WHITE hand-drawn strokes that self-draw, Permanent Marker + Nunito "
        "fonts, red/blue/green accent stamps, ~360x640 portrait. Focus ONLY on theme match.\n\n"
        "Final line must be exactly: VERDICT: MATCH  or  VERDICT: MISMATCH\n"
        "If MISMATCH, on the line before give: DETAIL: <what about palette/fonts/canvas is off>"
    ),
}

if len(sys.argv) < 3 or sys.argv[2] not in FOCUSES:
    print("usage: mimo_check.py <video.mp4> <focus>", file=sys.stderr)
    print("focuses: " + " | ".join(FOCUSES), file=sys.stderr); sys.exit(2)

VIDEO, FOCUS = sys.argv[1], sys.argv[2]
KEY = os.environ.get("OPENCODE_KEY")
if not KEY:
    print("ERROR: OPENCODE_KEY env var is required (no secrets hardcoded in this skill).", file=sys.stderr)
    sys.exit(1)

URL = "https://opencode.ai/zen/go/v1/chat/completions"
MODEL = "mimo-v2.5"

def b64(p):
    with open(p, "rb") as f: return base64.b64encode(f.read()).decode()

content = [
    {"type": "text", "text": FOCUSES[FOCUS]},
    {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64(VIDEO)}"}},
]
payload = {"model": MODEL, "messages": [{"role": "user", "content": content}], "temperature": 0.1}
req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
             "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) opencode-cli/1.0 whiteboard-reels"},
    method="POST")

print(f"[mimo_check] focus={FOCUS} video={VIDEO}", file=sys.stderr)
print(f"[mimo_check] sending WHOLE mp4 (never frames)...", file=sys.stderr)
try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode()[:400]}", file=sys.stderr); sys.exit(1)
except urllib.error.URLError as e:
    print(f"URL error (mimo hung/unreachable): {e}", file=sys.stderr); sys.exit(1)

out = data["choices"][0]["message"].get("content") or "(no content)"
print(out)
print(f"\n[mimo_check] usage: {json.dumps(data.get('usage', {}))}", file=sys.stderr)
