---
skill_name: coder-done-when-self-check
triggers:
  - Coder role about to write final `out_message.txt` or signal completion to the orchestrator
  - Coder role finishing an implementation that has a Planner `plan.md` with a `DONE WHEN:` line
  - Tuning a pipeline to reduce premature APPROVED / forced review-fix iterations
summary: Before declaring done, the Coder scores its own implementation against the Planner's `DONE WHEN:` line on a 0-10 scale; if the score is below 7, do another pass before handing off, and always log the score in `handoff.md`.
---

# Skill: Coder `DONE WHEN:` Self-Check

## Quick Reference
- Required action: score your implementation 0-10 against `plan.md`'s `DONE WHEN:` line, using the same rubric as `reviewer-exit-condition-scoring.md`.
- Threshold: `< 7` → do one more implementation pass before declaring done.
- Always log the score in `handoff.md` under a `## Coder Self-Check` section, even when `>= 7`.
- If `plan.md` has no `DONE WHEN:` line, log `CODER_SELF_CHECK_SCORE: N/A` with a one-sentence reason.

## When to Use
Every Coder invocation, immediately before writing `out_message.txt` or signaling completion to the orchestrator. Especially important in long pipelines where a Reviewer round-trip is expensive.

## Instructions

### Scoring Rubric (mirrors the Reviewer)
| Score | Meaning |
|-------|---------|
| 9-10  | Exit condition fully met; no observable gaps. |
| 7-8   | Exit condition substantially met; minor deviations that do not affect the user-visible outcome. |
| 4-6   | Exit condition partially met; at least one user-visible gap. **Do another pass.** |
| 0-3   | Exit condition not met or implementation is on the wrong track. **Do another pass.** |

### Output Placement in `handoff.md`
```
## Coder Self-Check
CODER_SELF_CHECK_SCORE: 8/10 -- All plan steps implemented; one optional cleanup deferred to a follow-up.
```

### Anti-Pattern to Avoid
Do not write `out_message.txt` with a self-check score you know is below 7 on the assumption that the Reviewer will catch it. This wastes a full review loop (the most expensive step in a KlodTalk pipeline) and inflates token cost. If you cannot raise the score, document precisely which sub-step of `DONE WHEN:` is unmet and why -- so the Reviewer / next Coder round can target it directly.

### Interaction with the Reviewer
- A self-check score `>= 7` is a starting point for the Reviewer, not a guarantee -- the Reviewer still scores independently per `reviewer-exit-condition-scoring.md`.
- A self-check score `< 7` (logged when no further pass was possible) is treated as a pre-declared WARNING; the Reviewer focuses there first instead of re-discovering the gap.

### Failure Mode to Avoid
Score against the Planner's `DONE WHEN:` line verbatim, not against your own preferred design. If the exit condition itself seems wrong, raise the disagreement as a `SUGGESTION:` in the coder output -- do not silently re-aim the implementation.

## Related
- `reviewer-exit-condition-scoring.md` -- the mirror rubric used by the Reviewer.
- `pipeline-handoff.md` -- the `handoff.md` convention this skill writes into.
- `teams/roles/coder.md` -- the role file that consumes this skill.

## Source
Anthropic Managed Agents Outcomes feature -- Doris26/claude-managed-agents-reference (github.com/Doris26/claude-managed-agents-reference); verification sentinel pattern -- aws-samples/sample-claude-code-agent-team (github.com/aws-samples/sample-claude-code-agent-team).
