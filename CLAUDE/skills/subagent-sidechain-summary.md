---
skill_name: subagent-sidechain-summary
triggers:
  - A sub-agent (Coder, etc.) is about to return an output artifact longer than ~200 lines
  - The orchestrator/reviewer is ingesting a large sub-agent output and context is ballooning
  - Reducing context accumulation in the parent session proactively, before compaction triggers
summary: "When a sub-agent's output artifact exceeds ~200 lines it writes a companion `<artifact>_summary.md` (structured: DONE / KEY_CHANGES / FILES_MODIFIED / RISKS / WHAT_TO_SKIP, max 50 lines); the consumer reads the summary first and the full artifact only if the summary flags it. Sub-agent-written, mid-pipeline — distinct from orchestrator-written stage handoff. Doc/convention only."
---

# Skill: Sub-Agent Sidechain Summary

## The Problem
Sub-agents that return large outputs (a long `coder_output.txt`) cause context to
accumulate in the calling orchestrator/reviewer session. Compaction
(`precompact-context-guard.md`) is **reactive** — it fires after context is already
full. A sidechain summary is **proactive**: it reduces what the parent ingests in
the first place.

## The Pattern
- Any sub-agent that produces an output artifact **> ~200 lines** writes a companion
  `<artifact>_summary.md` alongside the full artifact
  (e.g. `coder_output_summary.md` next to `coder_output.txt`).
- The summary is **structured** and **max 50 lines**:
  ```
  DONE: <one sentence — what this stage accomplished>
  KEY_CHANGES:
    - <bullet, the substantive changes>
  FILES_MODIFIED:
    - <path> — <one-line why>
  RISKS:
    - <anything the consumer must verify, or "none">
  WHAT_TO_SKIP: <which sections of the full artifact need NO review>
  ```
- The summary is **written by the sub-agent itself**, not the orchestrator.

## Consumer Discipline
- The orchestrator/reviewer reads `<artifact>_summary.md` **first**.
- It reads the full artifact **only** if `RISKS` or `WHAT_TO_SKIP` flags a section as
  requiring review.
- If the summary is absent (artifact <= ~200 lines), read the full artifact normally.

## Distinct From `pipeline-handoff.md`
| | sidechain summary (this skill) | `pipeline-handoff.md` |
|---|---|---|
| Written by | the sub-agent itself | the orchestrator |
| Timing | mid-pipeline, on large output | at a stage boundary |
| Consumed for | parent context reduction | next-role handoff |
They compose: a stage can write both a `handoff.md` (for the next role) and a
`_summary.md` (so the parent need not ingest its full output).

## Adoption Path
- Apply first to **Coder** (largest output) when `coder_output.txt` > 200 lines.
- Planner `plan.md` is already compact and rarely needs it.

## Cross-References
- `pipeline-handoff.md` — the orchestrator-written, stage-boundary variant (see table above).
- `precompact-context-guard.md` — the reactive compaction this proactively reduces pressure on.
- `large-output-spill.md` — spilling large raw output to a file; this skill adds a structured summary on top.

## Source
- VILA-Lab/Dive-into-Claude-Code — https://github.com/VILA-Lab/Dive-into-Claude-Code (⭐ 1,600):
  "sidechain summaries" pattern — sub-agents write a compact structured summary before returning,
  so the orchestrator reads the summary rather than the full output, avoiding context explosion.
