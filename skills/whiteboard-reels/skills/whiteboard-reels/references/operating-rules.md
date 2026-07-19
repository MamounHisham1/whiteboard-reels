# Operating rules for this pipeline

Hard-won rules for running the whiteboard-reels pipeline well. Follow these; they exist
because the alternatives were tried and produced worse output.

## Workflow
- **Start building immediately.** Skip ceremony (brainstorming docs, spec rituals) unless
  explicitly asked. Get to a first render fast.
- **Use sub-agent parallelism for batch work.** If N videos are requested, run N sub-agents
  — don't silently fall back to serial bash.
- **Report progress clearly** so the operator can interrupt when something is off.

## Verification method (the most important rules)
- **Send the WHOLE mp4 to mimo. Never cut the video into PNG frames.** Frame-cutting gives
  wrong answers and wastes calls. This is non-negotiable.
- **mimo is the validity gate.** Your own "it looks fine to me" is not enough — the build is
  only done when mimo says so.
- **Fix the exact element named in a defect report**, not a neighbor. If mimo says the
  rectangle is wrong, fix the rectangle — don't touch the label next to it.

## Defects and iteration
- **Never overwrite a render version.** Every render is preserved to `versions/video_vN.mp4`
  for review.
- **Kill hung mimo calls fast.** If a call exceeds ~5 minutes, kill it and retry once. If it
  hangs again, flag it in the run log and move on rather than burn time on a stuck call.

## Content
- **Invent original diagrams per topic.** Don't clone any single reference video's scenes —
  the shared things are the look (palette/fonts/mechanics), the voice, and the narrative
  rhythm, not the specific diagrams.
- **Keep the voice consistent across a series.** One voice across all videos in a batch.

## What not to do
- Don't ceremony-build around the task.
- Don't frame-cut for mimo.
- Don't guess at a fix — if you can't pin the defect, say so.
- Don't silently fall back from sub-agents to serial work.
