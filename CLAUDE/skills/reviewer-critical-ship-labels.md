---
skill_name: reviewer-critical-ship-labels
triggers:
  - Producing or auditing a reviewer verdict (`teams/roles/reviewer.md`)
  - A `CHANGES REQUIRED` review failed to trigger a fix round because no `BLOCKER:` line was present
  - Wiring the orchestrator's fix-round trigger to a single authoritative signal
summary: The reviewer emits one authoritative `REVIEW VERDICT: CRITICAL | SHIP` line that the orchestrator scans to decide a fix round. CRITICAL if any `BLOCKER:` line is present OR `EXIT_CONDITION_SCORE` is below 7; SHIP otherwise (the only non-blocking verdict). It is additive — `REVIEW RESULT:` and `BLOCKER:` lines stay for human readability — and resolves the gap where the orchestrator's BLOCKER-only scan ignored a low-score `CHANGES REQUIRED`.
---

# Skill: Reviewer CRITICAL/SHIP Two-State Verdict

## Quick Reference
- Required output line: `REVIEW VERDICT: CRITICAL` or `REVIEW VERDICT: SHIP`, placed directly under `REVIEW RESULT: ...` in `reviewer_output.txt`.
- Mapping:
  - `CRITICAL` if **any** `BLOCKER:` line is present **OR** `EXIT_CONDITION_SCORE` is a number **below 7**.
  - `SHIP` otherwise. **SHIP is the only non-blocking verdict.**
- `EXIT_CONDITION_SCORE: N/A` does **NOT** force CRITICAL. N/A + zero `BLOCKER:` lines → `SHIP` (Nightly Scout has no `DONE WHEN:` line, so N/A is normal there).
- The orchestrator scans the `REVIEW VERDICT:` line as the **single authoritative fix-round trigger**.

## The Problem It Solves
The reviewer historically emitted three partially-overlapping signals:
1. `REVIEW RESULT: APPROVED | CHANGES REQUIRED`
2. `BLOCKER:`-prefixed issue lines
3. `EXIT_CONDITION_SCORE: <n>/10`

The orchestrator's fix-round scan only fired on `BLOCKER:` lines. So a `CHANGES REQUIRED`
caused **only** by `EXIT_CONDITION_SCORE < 7` (with no `BLOCKER:` line) silently did **not**
trigger a fix round — a known footgun (see `feedback_reviewer_blocker_prefix_required.md`:
"CHANGES REQUIRED + score<7 alone do NOT trigger fix round").

`REVIEW VERDICT:` collapses the two trigger conditions (any BLOCKER **or** score<7) into one
line. The orchestrator scans that single line, so a low score can no longer slip through.

## Why Additive (not a replacement)
`REVIEW VERDICT:` does not remove `REVIEW RESULT:` or `BLOCKER:` lines:
- `BLOCKER:` lines remain the human-readable, file:line-cited evidence — and they still
  imply CRITICAL (any BLOCKER → CRITICAL).
- `REVIEW RESULT:` remains for back-compat and at-a-glance human reading.
- The three must stay consistent: CRITICAL ↔ `CHANGES REQUIRED`; SHIP ↔ `APPROVED`.

## Worked Examples
| BLOCKER lines | EXIT_CONDITION_SCORE | REVIEW VERDICT |
|---------------|----------------------|----------------|
| 0             | 9/10                 | SHIP           |
| 0             | 6/10                 | CRITICAL (score<7) |
| 2             | 8/10                 | CRITICAL (BLOCKER) |
| 0             | N/A                  | SHIP (N/A never forces CRITICAL) |
| 1             | N/A                  | CRITICAL (BLOCKER) |

## Related
- `reviewer-exit-condition-scoring.md` — the 0-10 scoring rubric and the `< 7` threshold this verdict folds in.
- `teams/roles/reviewer.md` — the role file that emits the verdict.
- `teams/orchestrator.md` "BLOCKER scan rule" — the orchestrator scan that consumes it: it fires a fix round on any `BLOCKER:` line **or** a `REVIEW VERDICT: CRITICAL` line, and treats `REVIEW VERDICT: SHIP` (with no BLOCKERs) as approved.
- `disprover-review-gate.md` — optional gate that verifies each `BLOCKER:` before it counts.

## Source
automagik-dev/genie — https://github.com/automagik-dev/genie (322★, observed 2026-06-26).
