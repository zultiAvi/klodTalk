---
skill_name: receiving-code-review
triggers:
  - Reviewer role starting a review of a Coder handoff
  - Reading `coder_output.txt` that contains a `## Review Request` block
  - Producing a deterministic, structured review pass over a defined risk surface
summary: When the Reviewer sees a `## Review Request` block in `coder_output.txt`, walk each Self-Assessed Risk Area and each Question explicitly, apply the standard `BLOCKER:` / `WARNING:` / `SUGGESTION:` taxonomy, and produce `reviewer_output.txt` with a section per risk -- not free-form prose.
---

# Skill: Receiving Code Review (Reviewer Side of the Handoff)

## Quick Reference
- Input: `## Review Request` block at the bottom of `/workspace/.klodTalk/team/current/coder_output.txt`.
- Output: `/workspace/.klodTalk/team/current/reviewer_output.txt`, with one section per Self-Assessed Risk Area.
- Severity prefixes (from `base.md`): `BLOCKER:`, `WARNING:`, `SUGGESTION:`.
- Companion skill: `requesting-code-review` (Coder side produces the request).

## When to Use
- The current pipeline step is a Reviewer role.
- `coder_output.txt` contains a `## Review Request` block (produced via the `requesting-code-review` skill).
- The team definition expects a structured review with explicit BLOCKER/WARNING/SUGGESTION outputs.

## Why It Matters

Free-form review prose is harder to act on: the Coder must re-parse it to find what blocks the commit, and downstream pipeline steps cannot reliably extract verdicts. Walking the Coder's named risk areas and producing one section per risk gives a one-to-one map from declared risk surface to review verdict -- which makes BLOCKER detection deterministic and makes review rounds reproducible across runs.

## Instructions

### 1. Parse the Review Request
Open `coder_output.txt` and locate the `## Review Request` block. If absent, fall back to standard Reviewer behavior (review the diff freely) and note in your output that the request block was missing.

If present, extract:
- The list under `### Self-Assessed Risk Areas`.
- The list under `### Questions for Reviewer` (may be absent or empty).
- The list under `### Files Modified` (cross-reference against `changed_files.txt`).

### 2. Walk Each Risk Area
For each Self-Assessed Risk Area, produce a section in `reviewer_output.txt`:

```
### Risk: <verbatim risk text from the request>
<Your review of this specific risk: what you checked, what you found.>

BLOCKER: <only if there is a real blocker tied to this risk>
WARNING: <only if there is a meaningful concern but not a blocker>
SUGGESTION: <optional improvement>
```

If you found no issue against a declared risk, say so explicitly:
```
### Risk: <risk text>
Reviewed -- no issues found. <One line on what you checked to reach that conclusion.>
```

### 3. Answer Each Question
For each entry under `### Questions for Reviewer`, produce a `### Question: <verbatim question>` section with a direct answer. Do not skip questions; if you cannot answer one, say so and downgrade to a WARNING that the Coder must resolve before commit.

### 4. Out-of-Scope Findings
If you find issues **not** covered by any declared risk area or question, add a final section:
```
### Out-of-Scope Findings
<List BLOCKER/WARNING/SUGGESTION items the Coder did not self-flag.>
```
A persistent gap between declared risks and out-of-scope findings is itself a signal -- consider raising a SUGGESTION asking the Coder to broaden their self-assessment next time.

### 5. Final Verdict
End `reviewer_output.txt` with the standard verdict token used by the team's `reviewer.md` (typically `APPROVED` or `BLOCKED`). The verdict is BLOCKED if **any** section contains a BLOCKER; otherwise APPROVED.

### What Not to Do
- Do not collapse multiple risks into one section -- the per-risk map is the whole point.
- Do not introduce a new severity vocabulary -- the `BLOCKER:` / `WARNING:` / `SUGGESTION:` prefixes from `base.md` are the canonical set.
- Do not silently drop a Coder question -- always answer or downgrade.

## Related
- `requesting-code-review` -- the Coder-side companion that produces the input block.
- `teams/roles/reviewer.md` -- the canonical Reviewer role definition; this skill is additive to its review criteria.
- `placeholder-guard` -- the stub/placeholder check belongs in the Reviewer's must-check list, independent of this handoff structure.

## Source
ithiria894/awesome-claude-code-workflows -- https://github.com/ithiria894/awesome-claude-code-workflows (two-skill code-review handoff pattern).
