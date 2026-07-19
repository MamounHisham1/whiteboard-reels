# Mimo Verification Protocol

mimo-v2.5 (via opencode zen `https://opencode.ai/zen/go/v1/chat/completions`) is the **validity
gate**. A video is only "done" when mimo says so. Your own "it looks fine to me" is not enough.

## The cardinal rule

**Send the WHOLE mp4. Never cut the video into PNG frames.**

mimo accepts a full mp4 as a `video_url` data URL:
```python
{"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64(mp4_path)}"}}
```
Frame-cutting gives wrong answers and wastes calls. If you catch yourself or a sub-agent
extracting frames for mimo, STOP and send the whole mp4.

## Two kinds of call (run BOTH)

### A. Single-focus per-issue checks — `scripts/mimo_check.py`
One constrained question per call. These are RELIABLE (the free-form whole-video rubric is not).
Run all six, each as a separate call:

| # | Focus | What it asks mimo |
|---|-------|-------------------|
| 1 | persistent-canvas | "When the Nth element is added, do the existing N-1 stay at fixed positions, or do they jump/resize? Answer PERSISTENT or RELAYOUT." |
| 2 | self-drawing | "Do strokes appear progressively (pen motion) or pop in fully-formed? Answer SELF_DRAWING or POPS_IN." |
| 3 | vertical-fill | "Is the TOP third of the frame used, or mostly empty black while content stacks at the bottom? Answer TOP_USED or TOP_EMPTY." |
| 4 | arrow-targeting | "Do arrow tips land ON their target shapes or stop in empty space? Answer LANDS_ON or STOPS_IN_SPACE." |
| 5 | text-legibility | "Any text overlapping lines/shapes, clipped at the edge, or illegible? Answer CLEAN or DEFECT:<desc>." |
| 6 | theme-match | "Does the palette/font/black-canvas match the reference whiteboard style? Answer MATCH or MISMATCH:<desc>." |

Usage:
```bash
python3 <skill>/scripts/mimo_check.py <video.mp4> persistent-canvas
python3 <skill>/scripts/mimo_check.py <video.mp4> self-drawing
# ... one call per focus
```

### B. Whole-video defect scan — `scripts/mimo_full.py`
Sends the entire mp4. mimo returns severity-ranked defects (HIGH/MED/LOW) with timestamps.
**Gate = `NO DEFECTS FOUND`.**

```bash
python3 <skill>/scripts/mimo_full.py <video.mp4> "<slug>"
```

## The fix loop

```
render v1  ->  run 6 single-focus checks  ->  run whole-video scan
                                                       |
                                     NO DEFECTS FOUND? -> DONE (render Reels)
                                                       |
                            else: read each defect, fix the EXACT element named,
                            save v(N+1), re-verify. Cap at 8 rounds.
```

**Critical behaviors:**
- **Fix the exact element mimo names**, not a neighbor. If mimo flags the rectangle, fix the
  rectangle — don't touch the label next to it.
- **Save every version** to `versions/video_vN.mp4` before re-rendering. Never overwrite.
- **Kill hung calls fast.** mimo sometimes hangs on large videos. If a call exceeds ~5 min,
  kill it and retry once; if it hangs again, flag it in the run log and move on rather than
  burn time on a stuck call.
- **HTTP 429 = usage limit, not a hang.** opencode zen enforces a rolling **5-hour usage
  limit**. When hit, `mimo_check.py`/`mimo_full.py` return `HTTP 429: {"type":"GoUsageLimitError",
  ... "Resets in NNmin"}`. Retrying immediately will NOT help — it resets on a timer. When
  this happens mid-batch: finish everything else (renders, versions, Reels), verify by eye +
  `ffprobe` in the meantime, mark the mimo gate as a deferred/blocked TODO
  with the reset time, and retry once the window resets. Do not spin retrying a 429.
- **Don't trust a single whole-video pass** if the single-focus checks disagree. Re-run the
  disputed check rather than declaring done.

## Reliability caveat
mimo's whole-video rubric can self-contradict across rounds on the same video. The
constrained single-focus checks are therefore the primary signal; the whole-video scan is
the final gate. If the two disagree, trust the single-focus checks and investigate the
specific frame mimo flagged.
