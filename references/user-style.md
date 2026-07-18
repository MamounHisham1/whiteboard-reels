# Working with the user of this skill

Learned from the session that produced this skill. Follow these or the user will get loud.

## Communicates
- Lowercase, fast-typing, frequent typos ("eveyrthing", "immedeiately"). ESL markers —
  dropped articles, verb-form slips. Arabic-speaking. Terse once work is underway
  ("done?", "still?", "2", "yeah reels quality all"). Escalates to "dude"/"man" + ALL CAPS +
  multiple exclamation marks when ignored.

## Wants
- **Speed over ceremony.** Skip brainstorming/spec rituals unless asked. Start building.
- **Sub-agent parallelism** for batch work. Notices when you silently fall back to serial
  bash. If they asked for N sub-agents, run N sub-agents.
- **mimo as the validity gate.** Your own "it looks fine" is not enough — the build is only
  done when mimo says so.
- **Every version preserved.** Never overwrite a render; the user watches all versions.
- **Consistent voice** across the series (Brian).

## Dislikes (ranked by how loud they got)
1. **Verification-method ignored.** The single loudest trigger: agents cutting the video
   into PNG frames instead of sending the WHOLE mp4 to mimo. NEVER do this.
2. **Fixes that don't land** / the same defect coming back. Get it right or say you can't.
3. **Fixing the wrong element.** When the user points at a specific defect, fix THAT exact
   element, not a neighbor. ("no the overloaded word was placed well, i mean remove the
   white rectangle around 'database'.")
4. **Slow/hung mimo calls.** Kill + retry fast. The user's patience for hung calls is near
   zero.
5. **Template-copying** instead of original content per topic.
6. **Snap-to-new-picture** scenes. Scenes must animate like a tablet pen on a persistent
   canvas, not be pictures added together.

## How they frame problems
- By concrete VISUAL OBSERVATION against a reference, often with a timing window
  ("the rectangle starts drawing at 17s and disappears around 56s"), and they redirect you
  to mimo for diagnosis ("mention that to mimo so it can tell u what/when/where").
- They delegate the engineering entirely (SVG coords, stroke-dashoffset, fonts) and never
  read code. They evaluate only the rendered output by eye + mimo.

## Net rule
You are an orchestrator that ships verified output. Do the work, use sub-agents at scale,
send whole videos to mimo, fix the exact element named, kill hung calls fast, preserve
versions. Don't ceremony-build, don't frame-cut, don't guess.
