---
skill_name: pipeline-signal-emitter-and-consumer
triggers:
  - Adding a new structured output token/line to a role file (e.g. a new `REVIEW VERDICT:`, `QA RESULT:`, `VALIDATION RESULT:` style marker)
  - A role emits a new signal but the pipeline behaves as if nothing changed
  - Reviewing a change that edits a `teams/roles/*.md` output contract
summary: A new structured signal in a role's output is a NO-OP until the orchestrator's scan rule is taught to read it. The role that EMITS the token and the orchestrator rule that CONSUMES it must be wired in the same change, or the feature is half-built and silently inert.
---

# Skill: Wire Both the Emitter and the Consumer of a Pipeline Signal

## The Rule
KlodTalk's control flow is split across two layers:
- **Emitter** — a `teams/roles/<role>.md` file tells a sub-agent to write a structured line
  (e.g. `REVIEW VERDICT: CRITICAL`, `TEST_RESULT: PASS`, `VALIDATION RESULT: APPROVED`).
- **Consumer** — a *prompt rule* in `teams/orchestrator.md` (NOT Python code) scans that output
  and decides the next pipeline step (fix round, proceed, replan, etc.).

If you add or change a signal in the emitter but do not update the consumer scan rule, the
orchestrator keeps making decisions on the OLD signal — the new line is written but ignored.
The feature looks done (the file is edited, the skill exists) but is functionally inert.

## Why this footgun is easy to hit
The decision logic lives in **prose**, not code. `grep BLOCKER server/*.py` returns nothing —
the BLOCKER/verdict scan is an orchestrator-prompt rule under "Review Loops" in
`teams/orchestrator.md`. So "edit the reviewer" feels complete, but the consumer is in a
different file that is easy to forget. (This is exactly how the `REVIEW VERDICT:` change shipped
half-wired in the 2026-06-28 nightly until the reviewer caught it.)

## Checklist when adding/changing a role output signal
1. **Emitter:** update `teams/roles/<role>.md` output template + the rule that maps state → token.
2. **Consumer:** update the matching scan rule in `teams/orchestrator.md` (search for the relevant
   loop section: "BLOCKER scan rule", "Validator Review Loops", etc.) so it reads the new token.
3. **Back-compat:** if additive, confirm the old tokens still work so the change does not break
   other teams that have not adopted the new signal.
4. **Cross-reference:** have the new skill's "Related" section name BOTH files (emitter + consumer)
   so the next editor sees both halves.
5. **Verify:** there is no Python to test — re-read the orchestrator rule and confirm it branches
   on the new token. A reviewer should treat "emitter edited, consumer not" as a BLOCKER.

## Related
- `reviewer-critical-ship-labels.md` — a concrete instance (REVIEW VERDICT wired into the BLOCKER scan rule).
- `pipeline-handoff.md`, `pipeline-stage-isolation.md` — other cross-stage contracts.
- `reviewer-exit-condition-scoring.md` — the score signal that the verdict folds in.
