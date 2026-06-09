---
skill_name: scout-evaluator-dedupe-existing-work
triggers:
  - Running the nightly scout idea_evaluator (or any recurring research pipeline)
  - Findings overlap with features/skills shipped on prior nightly runs
  - Picking the "top N" ideas to implement from accumulated scout findings
summary: "Before recommending a scout idea, prove it is NOT already done: grep CLAUDE/skills/ and run git log; reject or downscope anything already covered."
---

# Skill: Scout Evaluator — Reject Already-Implemented Ideas

## When to Use
The nightly scout runs every night against the same channels, so scouts re-surface the same Anthropic releases and popular repos for days. Without a dedupe gate the evaluator keeps recommending — and the coder keeps re-implementing — work that landed on a previous night (e.g. `fallbackModel`, model-ID retirement audit, Agent-SDK credit billing, glob deny-rules, JSONL dedupe, local token analytics have all been done already).

## Instructions
1. **Before scoring any finding, check whether it already exists:**
   - `ls /workspace/CLAUDE/skills/` and `grep -rl -i "<keyword>" CLAUDE/skills/` for the feature's keywords.
   - `git log --oneline -15` to see recent nightly commits (titles like `Nightly Scout YYYY-MM-DD: ...` and `Add skills: ...`).
   - For config/model claims, `grep` the actual files (`config/`, team `.md`s) to confirm the current state rather than trusting the finding's framing.
2. **Classify each finding:**
   - **Already implemented** → put it under `## Rejected Ideas` with the exact skill/commit that covers it. Do NOT give it a top slot.
   - **Partially done** → recommend ONLY the concrete net-new increment that does not yet exist (e.g. a 5-hour-window view over already-recorded token data), or defer.
   - **Net-new** → eligible for a top slot.
3. **Pick top candidates only from net-new (or net-new-increment) ideas.** Prefer small, self-contained team/role/util/skill edits over core-server changes.
4. In `evaluated_ideas.md`, the `## Rejected Ideas` section should explicitly name the covering skill/commit for each already-done item — this is the audit trail that proves the dedupe gate ran.

## Related
- `github-mcp-scout.md` — reliable star/date data so "recency" claims aren't hallucinated.
- `fresh-context-evaluator.md` — review-stage context hygiene (different stage, complementary).
