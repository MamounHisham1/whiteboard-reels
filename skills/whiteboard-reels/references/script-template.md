# script.json Template & Narrative Structure

## Schema
```json
{
  "title": "SYSTEM DESIGN",
  "headline": "<TOPIC NAME>",
  "voice": "nPczCjzI2devNBz1zQrb",
  "scenes": [
    { "id": "s1", "text": "..." },
    { "id": "s2", "text": "..." }
  ]
}
```
- `title` is always `"SYSTEM DESIGN"` (the series identity).
- `headline` is the topic (e.g. `"BLOOM FILTERS"`, `"RAFT CONSENSUS"`).
- `voice`: ElevenLabs voice id. Brian = `nPczCjzI2devNBz1zQrb`. If you know you'll fall
  back to Kokoro, set `"am_michael"` so the TTS script picks the right path.
- `scenes`: 15-18 entries, each `{id: "sN", text: "<one narration beat>"}`. Ids are `s1`,
  `s2`, ... contiguous. `theme.ts` keys scene timing off these ids.

## Narrative arc (15-18 scenes, ~150-165s total)

Each scene is ONE narration beat (~6-12s of audio). Match the reference's rhythm:

**Chapter 1 — THE PROBLEM (scenes s1..sN, roughly s1-s10)**
1. Set the stage — the system before the technique exists. ("Your app has one database...")
2. Growth/pressure — why the simple version breaks. ("...fifty million users across four shards.")
3. The rule — the naive approach. ("user_id % four.")
4. Concrete walk-through — show it working on two examples (two named users, two outcomes).
5. "Works great." — brief calm beat.
6. The break — a change that wrecks the naive approach. ("Now add a FIFTH shard.")
7-9. The remapping cascade — show the chaos. Each user's mapping flips.
10. **NIGHTMARE stamp** (red, Permanent Marker, rotated). "This is a nightmare."

**Title card (scenes sN+1, sN+2)** — hard clear-to-black, then the topic headline stamps in.

**Chapter 2 — THE SOLUTION (scenes sM..s17)**
- Introduce the technique by name (the headline).
- Explain the mechanism with original diagrams specific to this topic.
- Show the worst-case from Chapter 1 now resolved cleanly.
- End with a green checkmark and a one-line closer ("That's <technique>.")

## Length targets
- Each scene's audio is ~6-12s. Total ~150-165s after 0.12s gaps between scenes.
- If a scene's text is too long it'll blow the budget; keep each beat to 1-2 short sentences.
- The reference video is ~165s; match within +/-15s.

## Content originality
This is a SERIES, not a template. Each video invents its own diagrams and scene structure to
fit its topic — do NOT clone the consistent-hashing scenes. The only shared things are the
look (palette/fonts/mechanics), the voice, and the narrative rhythm described above.
