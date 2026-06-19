---
skill_name: coder-confidence-gate
triggers:
  - Coder finishes a pipeline stage and the orchestrator is about to invoke the Reviewer
  - Wanting to catch low-confidence Coder output before a full Reviewer round is spent
  - Tuning the nightly pipeline to reduce wasted Coder/Reviewer iterations
summary: "Coder emits a CODER_CONFIDENCE/KNOWN_GAPS/RISK_FLAGS block at the end of its output; if confidence < 6 the orchestrator requests a fix pass BEFORE invoking the Reviewer — a pre-Reviewer gate that complements the post-Reviewer disprover gate."
---

# Skill: Coder Confidence Gate (pre-Reviewer)

## When to Use
Every Coder invocation in a team pipeline that has a Reviewer stage. The gate runs
*after* the Coder writes `coder_output.txt` and *before* the orchestrator invokes the
Reviewer — cheaper than discovering the gap in a full review round.

## Instructions

### (a) Self-assessment block format
The Coder emits this short structured block at the END of `coder_output.txt`:
```
CODER_CONFIDENCE: 0-10
KNOWN_GAPS: <one line — unmet sub-steps, untested paths, or "none">
RISK_FLAGS: <one line — risky areas the Reviewer should focus on, or "none">
```

### (b) Threshold rule
- `CODER_CONFIDENCE < 6` → the orchestrator requests ONE Coder fix pass **before**
  invoking the Reviewer. The Coder re-runs targeting its own `KNOWN_GAPS`.
- `>= 6` → proceed to the Reviewer as normal.
- If a fix pass cannot raise it to >= 6, proceed anyway with the low score logged so
  the Reviewer focuses on the declared gaps first (do not loop indefinitely).

### (c) How this differs from existing gates
- `coder-done-when-self-check.md` — a DONE-WHEN self-score logged in `handoff.md`,
  scored against the Planner's exit condition. The confidence gate is a *pipeline-stage*
  gate keyed on the Coder's own self-rated confidence, not the plan's exit condition;
  they are complementary, not duplicates. (A 0-10 DONE-WHEN score and a 0-10 confidence
  score can differ — confidence captures uncertainty the exit-condition check misses.)
- `reviewer-exit-condition-scoring.md` — runs INSIDE the Reviewer (after it is invoked).
- `disprover-review-gate.md` — a POST-Reviewer gate that filters false-positive BLOCKERs.
- This skill fills the **PRE-Reviewer Coder→Reviewer gap** none of the above cover.

## Related
- `coder-done-when-self-check.md`, `reviewer-exit-condition-scoring.md`, `disprover-review-gate.md`
- `teams/roles/coder.md` — the role that emits the block.

## Source
Kanevry/session-orchestrator — https://github.com/Kanevry/session-orchestrator (35 stars), inter-wave confidence-scored quality gates.
