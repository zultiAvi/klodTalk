---
skill_name: reviewer-exit-condition-scoring
triggers:
  - Producing a reviewer verdict (`teams/roles/reviewer.md`)
  - Auditing whether an APPROVED verdict matches the plan's exit condition
  - Tuning the nightly review-fix loop for fewer false approvals
summary: Reviewer scores the implementation against the plan's `DONE WHEN:` line on a 0-10 scale; scores below 7 are treated as a BLOCKER regardless of other findings.
---

# Skill: Reviewer Exit Condition Scoring

## Quick Reference
- Required output line: `EXIT_CONDITION_SCORE: <n>/10` followed by a one-sentence justification.
- Threshold: `< 7` → treat as `BLOCKER` regardless of other findings → forces `REVIEW RESULT: CHANGES REQUIRED`.
- Rubric source: the `DONE WHEN:` line in the Planner's `plan.md`.

## When to Use
Every reviewer invocation that has a `plan.md` with a `DONE WHEN:` exit condition. If the plan has no `DONE WHEN:` line, write `EXIT_CONDITION_SCORE: N/A` and a one-sentence reason.

## Instructions

### Scoring Rubric
| Score | Meaning |
|-------|---------|
| 9-10  | Exit condition fully met; no observable gaps. |
| 7-8   | Exit condition substantially met; minor deviations that do not affect the user-visible outcome. |
| 4-6   | Exit condition partially met; at least one user-visible gap. **Blocker.** |
| 0-3   | Exit condition not met or implementation is on the wrong track. **Blocker.** |

### Threshold Rationale
The 7/10 floor allows minor stylistic or naming deviations to pass without triggering a rework loop, while catching missed exit conditions that would otherwise be approved alongside well-intentioned but off-target work.

### Output Placement
Add the line to the reviewer output template, immediately after the `## Verdict` section:
```
## Exit Condition Check
EXIT_CONDITION_SCORE: 8/10 — All plan steps implemented; one optional follow-up deferred.
```

### Failure Mode to Avoid
Do not score against your own preferred design — score against the Planner's `DONE WHEN:` line verbatim. If you disagree with the exit condition, raise a `SUGGESTION:` separately.

## Related
- `teams/roles/reviewer.md` — the role file that consumes this skill.
- `requesting-code-review.md` / `receiving-code-review.md` — review-loop framing.

## Source
Anthropic Multiagent Sessions and Outcomes public beta — https://platform.claude.com/docs/en/release-notes/overview (platform.claude.com/docs).
