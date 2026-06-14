---
skill_name: disprover-review-gate
triggers:
  - Reviewer emitted one or more `BLOCKER:` lines and a Coder fix round is about to start
  - Wanting to cut false-positive BLOCKERs before they cost a rework loop
  - Tuning the nightly review-fix loop for fewer wasted Coder/Reviewer iterations
summary: "Optional gate: each `BLOCKER:` is checked by a read-only disprover sub-agent that tries to refute it against the code and emits `CONFIDENCE: <0-100>`; below-threshold BLOCKERs are demoted to `WARNING:` and do not trigger a fix round."
---

# Skill: Disprover Review Gate

## When to Use
- The reviewer wrote at least one `BLOCKER:` line in `reviewer_output.txt` and iterations remain.
- The team is review-heavy and false-positive BLOCKERs (the most-documented reviewer pain) are burning Coder fix rounds.
- Opt-in only — skip for trivial tasks or when no BLOCKER lines were found (the loop already approves).

## Instructions

### The Disprove-Then-Threshold Pattern
1. Scan `reviewer_output.txt` for every line starting with `BLOCKER:`.
2. For each BLOCKER, spawn a **read-only** verifier sub-agent (see `teams/roles/disprover.md`; Read/Grep/Glob only — no Bash/Write/Edit). Its sole job is to *try to disprove* the finding against the actual code.
3. Each verifier emits exactly:
   ```
   BLOCKER: <verbatim finding>
   CONFIDENCE: <0-100>
   VERDICT: <one line — confirmed real, or refuted because ...>
   ```
   `CONFIDENCE` = how confident the finding is a *genuine* defect (100 = certainly real, 0 = certainly a false positive).
4. **Threshold = 80 (recommended).** BLOCKERs with `CONFIDENCE >= 80` survive and trigger the Coder fix round as usual. BLOCKERs scoring below threshold are **demoted to `WARNING:`** (informational only) and do NOT trigger a fix round.
5. If, after demotion, zero `BLOCKER:` lines remain, treat the review as approved (per the orchestrator's existing BLOCKER-scan rule).

### Discipline
- The disprover never edits code or files — it only reads and reports. Demotion is a tool-restricted, auditable step, not the reviewer second-guessing itself.
- Log each verdict + confidence to `orchestrator_log.md` so the demotion decision is auditable.
- Keep it opt-in: the default loop is unchanged unless the orchestrator runs this gate.

## Related
- `teams/roles/disprover.md` — the read-only verifier role.
- `teams/roles/reviewer.md` / `reviewer-exit-condition-scoring.md` — produce the BLOCKERs this gate filters. The reviewer's "Evidence Requirement" (every BLOCKER cites a `file:line` actually read) makes each finding cheaper for this gate to confirm or refute.
- `fresh-context-evaluator.md` — clean-context re-read (complementary, not refutation).

## Source
- VoltAgent/awesome-claude-code-subagents — https://github.com/VoltAgent/awesome-claude-code-subagents (confidence-scoring disprover subagent pattern).
- anthropics/claude-code — https://github.com/anthropics/claude-code (code-review plugin / `/ultrareview` refute-then-threshold writeups).
