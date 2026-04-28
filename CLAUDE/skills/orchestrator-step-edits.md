# Skill: Editing Orchestrator Pipeline Steps

## When to Use
When modifying numbered pipeline steps in `teams/orchestrator.md` (e.g., changing Step 6 behavior, inserting Step N.5, adjusting reporting requirements) or changing what files the orchestrator must produce.

## Instructions

### Anatomy of orchestrator.md
The file is a single long instruction document Claude reads as the orchestrator prompt. Each `## Step N:` heading defines a phase the orchestrator runs. Subsections cover:
- Step 1–3: classify, extract team rules, run pipeline (review loops live inside Step 3).
- Step 4: Reporting (progress, history logging, broadcasts).
- Step 5: Output files (table the orchestrator must produce).
- Step 6+: post-pipeline reflection (skills, instincts).

### When editing a numbered step
1. **Replace, do not duplicate** — when rewriting `## Step N:`, ensure exactly one heading with that number remains. `grep -n "^## Step" orchestrator.md` after editing to verify ordering.
2. **Preserve neighbors** — do not collapse adjacent steps. If you insert `Step N.5`, place it strictly between Step N and Step N+1.
3. **Update the Step 5 Output Files table** if your edit adds or removes a file the orchestrator writes.
4. **Update broadcast sections** (Reporting subsections under Step 4) if the new step produces user-facing output that should be streamed.

### When inserting a new step
- Number it with `.5` suffix (e.g., `Step 6.5`) rather than renumbering everything — keeps diffs clean.
- Match the formatting of neighboring steps: `## Step N: <Name>` then numbered list of actions.
- If the step writes a file, list it in Step 5's table.
- If the step produces user-facing output, add a Broadcast subsection in Step 4 (atomic write pattern: `.tmp` then rename).

### When adding skill/instinct rules
- Skill rules live in `## Step 6:`; instinct rules live in `## Step 7:`. Keep them separate.
- Document the convention in `teams/CLAUDE.md` so future contributors can find it without reading orchestrator.md end-to-end.

### Verification checklist after editing
- `grep -c "^## Step" orchestrator.md` — count matches your expectation.
- Step 7 (Project Instincts) is still present and unchanged unless you intentionally edited it.
- Markdown lists and code fences are balanced (no orphan ``` left over from a replacement).
