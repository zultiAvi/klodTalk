---
skill_name: requesting-code-review
triggers:
  - Coder role finishing its implementation step and handing off to a Reviewer
  - Any pipeline step that ends in `coder_output.txt` and is followed by a review step
  - Drafting the closing section of a coder output for predictable downstream review
summary: When the Coder finishes a change, append a structured `## Review Request` block to `coder_output.txt` that lists the change summary, files modified, self-identified risk areas, and specific questions for the Reviewer -- so the Reviewer applies criteria deterministically against named risks instead of free-form scanning.
---

# Skill: Requesting Code Review (Coder Side of the Handoff)

## Quick Reference
- Where: as the **final section** of `/workspace/.klodTalk/team/current/coder_output.txt`.
- Section heading: `## Review Request` (exact spelling -- the Reviewer side keys off this).
- Required sub-fields: `Change Summary`, `Files Modified`, `Self-Assessed Risk Areas`, `Questions for Reviewer`.
- Companion skill: `receiving-code-review` (Reviewer side consumes this block).

## When to Use
- The Coder role has finished implementing changes and is about to commit.
- The current team pipeline includes a downstream Reviewer step (the common case for `cross-modules`, `plan-code-qa-review`, `tdd`, `refactor`, `security`).
- You want the Reviewer's BLOCKER/WARNING/SUGGESTION findings to be tied to risks you already identified, rather than re-discovered ad hoc.

## Why It Matters

Without a structured handoff, the Reviewer receives a prose summary of what changed and applies its own review heuristics from scratch. Two reviewers (or two runs of the same reviewer) may land on different findings purely because the entry points to the diff were different. A structured `## Review Request` block names the risk surface up front and gives the Reviewer a checklist to apply systematically -- reducing variance and making BLOCKER detection more reliable.

## Instructions

Append the following block to `coder_output.txt` after the standard sections (Files Changed, Pre-commit Self-Check, etc.):

```
## Review Request

### Change Summary
<1-3 sentences: what behavior changed and why. Do NOT restate the diff line-by-line.>

### Files Modified
- path/to/file_a.py -- <one line on what changed in this file>
- path/to/file_b.md -- <one line>
- ...

### Self-Assessed Risk Areas
- <risk 1>: <why it is a risk and what specifically to look at>
- <risk 2>: <...>
- (If you genuinely identify no risk, write "None -- documentation-only change" or similar. Do not pad.)

### Questions for Reviewer
- <specific yes/no or focused question, if any>
- <e.g., "Does the new env-var precedence match the docker-claude-stability skill's recommendation?">
- (Omit this sub-section if there are no specific questions.)
```

### Guidelines for Each Sub-Field
- **Change Summary**: high-level intent, not a diff recap. The Reviewer will read the diff -- you don't need to retype it.
- **Files Modified**: the same list that appears in your `changed_files.txt`, annotated with one line each. Helps the Reviewer prioritise.
- **Self-Assessed Risk Areas**: be honest. Common risk categories: security (auth, secrets, input validation), state (race conditions, idempotency), correctness (edge cases, error paths), compatibility (CLI version pin, env var support), scope (touched files beyond the plan).
- **Questions for Reviewer**: only when there's a real ambiguity. Don't manufacture questions.

### What Not to Do
- Do not put this block in a separate file -- the Reviewer reads `coder_output.txt`.
- Do not skip `Self-Assessed Risk Areas` -- "None" is acceptable but the heading must be present so the Reviewer's parser doesn't fall back to free-form scanning.
- Do not pre-empt the Reviewer's verdict ("I think this is fine") -- state risks, not conclusions.

## Related
- `receiving-code-review` -- the Reviewer-side companion that consumes this block.
- `placeholder-guard` -- the pre-commit self-check; its results belong in their own `## Pre-commit Self-Check` section, not inside `## Review Request`.
- `teams/roles/coder.md` -- the canonical Coder role definition; this skill is additive to it.

## Source
ithiria894/awesome-claude-code-workflows -- https://github.com/ithiria894/awesome-claude-code-workflows (two-skill code-review handoff pattern).
