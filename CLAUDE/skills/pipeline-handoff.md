---
skill_name: pipeline-handoff
triggers:
  - Completing a pipeline stage that hands off to the next role (Planner → Coder, Coder → Reviewer)
  - Long task with many BTW messages accumulating context
  - Reducing per-stage token overhead in a multi-agent pipeline
summary: Optional `.klodTalk/team/current/handoff.md` convention — each pipeline stage writes a compact, structured summary so the next role can skip re-reading the full accumulated context.
---

# Skill: Pipeline Handoff (Inter-Agent Context Compaction)

## Quick Reference
- File path: `/workspace/.klodTalk/team/current/handoff.md`
- Optional: if present, the next role reads it first; if absent, normal context flow applies.
- Written by the **outgoing** stage (Planner writes for Coder; Coder writes for Reviewer).

## When to Use
- The task accumulated many BTW messages or the Planner's `plan.md` is long.
- The pipeline includes a review-fix loop where the same context would otherwise be re-read each iteration.
- You want a deterministic, auditable summary line that downstream tooling can grep.

## Instructions

### Handoff File Format
```
STAGE: <role name>
DONE: <one sentence of what was accomplished>
KEY_DECISIONS:
  - <bullet, max 5 items>
FAILED_APPROACHES:
  - <approach> — <why it failed>   (chronological one-liners, or "none")
NEXT_AGENT_NEEDS: <what the next role must know to skip re-reading the full context>
OPEN_ITEMS: <unresolved questions or risks, or "none">
```

`FAILED_APPROACHES` records every dead end already tried (the most expensive thing for the next role to rediscover), so the next stage/iteration does not re-derive it.

### Producer Discipline
- Write `handoff.md` after the stage's primary output (`plan.md`, `coder_output.txt`, ...), not instead of it.
- Keep it under ~30 lines. If it is longer, the stage is doing too much.
- Do not include code blocks — point to the file paths instead.
- **`FAILED_APPROACHES` is append-only**: across review-fix iterations, add new dead ends below the existing ones — never overwrite or trim the list. It accumulates within a task so the log survives every fix round. One line per entry; point to file paths, not code.

### Consumer Discipline
- Read `handoff.md` first, then read only the artifacts it references.
- **Read `FAILED_APPROACHES` before attempting a fix** so you do not retry an approach the reviewer (or a prior iteration) already rejected.
- If `handoff.md` is absent, follow the role's normal context-loading instructions.
- If `handoff.md` contradicts the primary artifact (e.g., `plan.md`), trust the primary artifact and flag the contradiction.

## Related
- `requesting-code-review.md` and `receiving-code-review.md` — review-loop handoff specifics.
- `selective-git-staging-nightly.md` — companion convention for nightly pipelines.
- `subagent-sidechain-summary.md` — the sub-agent-written, mid-pipeline variant (sub-agent summarizes its own large output for the parent, vs. this skill's orchestrator-written stage handoff).

## Source
- mattpocock/skills handoff pattern — https://github.com/mattpocock/skills (star count flagged as implausible by the idea evaluator; treated as a standalone pattern rather than a vetted repo).
- `FAILED_APPROACHES` field: REMvisual/claude-handoff — https://github.com/REMvisual/claude-handoff (~19 stars, v2.0.0 2026-04-21), which records every failed approach chronologically as "the most expensive thing to rediscover".
