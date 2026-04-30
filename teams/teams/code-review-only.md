# Team: Code-Review-Only

Single-agent review team. Performs a thorough code review of the current branch without making any code changes. Produces a structured report suitable for PR review or code audit.

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| reviewer | reviewer | opus |

## Pipeline

1. **reviewer** — Run `git diff origin/<base_branch>..HEAD` to see the full diff. Read every changed file in full — do not rely on diff context alone. Produce a structured report with the following sections:
   - **Executive Summary** (3-5 sentences): What these changes do, overall quality assessment.
   - **Critical Issues** (blockers): Must be fixed before merge.
   - **Major Issues** (significant but not blocking): Should be fixed but not a hard blocker.
   - **Minor Issues** (style/nitpicks): Nice to fix, low priority.
   - **Positive Notes**: What was done well.
   - **Merge Verdict**: One of APPROVE / REQUEST CHANGES / NEEDS DISCUSSION, with a one-sentence justification.

## Special Rules

**These rules apply to ALL pipeline members and to the orchestrator itself. The orchestrator MUST include these Special Rules verbatim in every sub-agent prompt.**

- **No code**: The reviewer must NOT create, modify, or delete any source files. This team produces a review report only.
- **No commits**: No git commits at any pipeline stage.
- **Always COMPLEX**: Always classify the task as COMPLEX. Never take the SIMPLE path. Never implement directly.
- **Read-only analysis**: The reviewer reads code and produces written analysis. Do not frame output in terms of code changes to make — frame it as findings for the human to act on.
- **Fixed metadata**: Always write plan_meta.txt with: IS_SIMPLE=false, REVIEW_ITERATIONS=0, COMPLEXITY=medium, NEEDS_EXECUTION=false.
