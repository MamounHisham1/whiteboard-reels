# Why a Local Remotion Project (not the cloud `belt` CLI)

The bundled `remotion-render` skill renders TSX via a cloud CLI (`belt` / inference.sh):
you pass raw component code, it returns an MP4. That's great for one-off animations.

This skill does NOT use it for the actual video builds, because:

1. **Reference fidelity needs the full project.** The whiteboard look comes from a specific
   `remotion-project/` with bundled Primitives (`Cylinder`, `DrawLine`, `Clock12`,
   `ArcCreep`, `RedX`), an exact palette in `theme.ts`, hand-loaded Google Fonts, a TTS
   pipeline that drives scene timing, and `<Audio>` wired to `public/narration.mp4`. The
   cloud CLI would throw all of that away and you'd lose the persistent-canvas feel.

2. **Verification needs a stable artifact.** mimo reviews a finished mp4 that has synced
   narration. The cloud CLI has no notion of audio-driven timing.

3. **Versions.** Every render is saved to `versions/video_vN.mp4` for review. The cloud CLI
   doesn't manage that.

## So when DO we use `remotion-render`?
- As a **quick sketch pad** — render a single primitive or motion test in isolation before
  wiring it into the local project.
- For **non-series** one-off animations that don't need the whiteboard identity.

## Dependency check
The skill checks for `remotion-render` in your skill dirs on load:
```bash
ls ~/.zcode/skills/remotion-render ~/.agents/skills/remotion-render ~/.claude/skills/remotion-render 2>/dev/null
```
If it's missing in all three, you can install the official one:
```bash
npx skills add belt-sh/cli   # then the remotion-render skill is available via `belt`
```
...but again, the actual builds here use `npx remotion render` inside the local project.

## Local runtime requirements
- `node` (for npx/remotion)
- `npx remotion` (Remotion CLI; installed per-project via the pinned `package.json`)
- `python3`, `ffmpeg`/`ffprobe` (TTS duration + audio concat)
- `curl` (mimo calls — though `scripts/*.py` use urllib)
