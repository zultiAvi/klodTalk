---
skill_name: multi-perspective-review-checklist
triggers:
  - The reviewer sub-agent is about to inspect a large or multi-file coder change
  - Reorganizing teams/roles/reviewer.md "What to Review" must-check items
  - A review approved a change but later missed a security or performance defect
summary: "Run code review as four explicit independent passes — Architecture, Security, Performance, Quality — before a single synthesized verdict, so a one-perspective scan can't miss a whole defect category. Sourced from wshobson/commands' full-review pattern."
---

# Skill: Multi-Perspective Review Checklist

## Quick Reference
- Pattern: decompose review into four independent passes, then synthesize ONE verdict.
- The four passes: **Architecture** → **Security** → **Performance** → **Quality**.
- Applied in `teams/roles/reviewer.md` "What to Review" (must-check items grouped under the four passes).
- This is a CHECKLIST reorganization only — it does NOT add new BLOCKER categories or change the `REVIEW VERDICT:` / `BLOCKER:` / `WARNING:` output conventions (see `reviewer-critical-ship-labels.md`).
- A new reviewer output token is inert unless the orchestrator scan rule is wired too (instinct #49 / `pipeline-signal-emitter-and-consumer.md`); this pattern emits NO new token, so no orchestrator change is needed.

## When to Use
When reviewing a large or multi-file coder change, or when auditing `reviewer.md` so its must-check items are grouped by analytical lens instead of a flat list. The risk this guards against: a single-perspective skim (e.g. only checking correctness) that silently misses an entire category such as a security hole or an O(n^2) hot path.

## Instructions
Make four separate passes over the changed files. Do not collapse them — each pass asks a different question, so a defect invisible to one lens is caught by another. Synthesize a single `REVIEW VERDICT:` only after all four.

1. **Architecture Pass** — structure, contracts, plan adherence, completeness. Does the code do what was requested? Are all plan steps implemented? Do interfaces/contracts hold?
2. **Security Pass** — injection vulnerabilities, exposed/hardcoded secrets, unsafe operations, permission-model violations.
3. **Performance Pass** — algorithmic complexity, I/O patterns, context/token cost, Docker resource usage.
4. **Quality Pass** — readability, naming, function length, stub/placeholder detection, test coverage, error handling, style consistency.

Then synthesize: emit the existing `REVIEW RESULT:` + `REVIEW VERDICT:` + prefixed `BLOCKER:`/`WARNING:`/`SUGGESTION:` lines exactly as `reviewer.md` already specifies. The passes organize WHERE you look, not WHAT you output.

## Cross-References
- `reviewer-critical-ship-labels.md` — the `REVIEW VERDICT: CRITICAL | SHIP` conventions these passes feed into (unchanged by this pattern).
- `pipeline-signal-emitter-and-consumer.md` — why this stays a checklist-only change (no new output signal → no orchestrator scan rule needed).
- `disprover-review-gate.md` — optional gate that verifies each `BLOCKER:` against the code.

## Source Attribution
- `wshobson/commands` (community): https://github.com/wshobson/commands (~2,500 stars) — its `full-review` slash command decomposes review into architecture / security / performance / quality sub-passes before a final synthesis.
