---
skill_name: selective-git-staging-nightly
triggers:
  - Committing inside a nightly/automated pipeline (e.g., nightly_scout, system_routine)
  - Writing a Coder role that needs to commit a known file list
  - Diagnosing a commit that swept in unrelated pre-existing modifications
summary: In automated pipelines, run `git status` before staging and pass only the explicit file list to `git add` — never `-A`/`.` — so pre-existing uncommitted edits do not silently ride in.
---

# Skill: Selective Git Staging in Nightly Pipelines

## Quick Reference
- Always run `git status` BEFORE `git add` and inspect for unrelated modifications.
- Pass **explicit relative paths** to `git add`; never use `git add -A`, `git add .`, or `git add -u` in automated jobs.
- If unrelated changes are present, either skip them (preferred) or list them under "deviations" in `coder_output.txt`.

## When to Use
- Coder/fix roles inside the `system_routine` session or any nightly team (nightly_scout, optimizer, tdd) that commits autonomously.
- Any pipeline where the workspace persists across runs (KlodTalk's per-project Docker images keep working-tree edits between sessions).
- When `.klodTalk/instincts.md` or other tracked files inside the gitignored `.klodTalk/` tree may carry uncommitted modifications from prior runs.

## Why It Matters

KlodTalk reuses workspace volumes across nightly runs. A previous human edit or a previous role's mid-run modification can sit uncommitted on disk indefinitely. The very first commit from a new pipeline run will sweep it in if `git add` is given a broad pattern, producing undisclosed scope-creep commits and confusing review history.

`.klodTalk/instincts.md` is the canonical landmine: the directory is gitignored, but the file is tracked — so `git add .klodTalk/instincts.md` succeeds and quietly stages any prior working-tree drift.

## Instructions

1. Before staging, run `git status --short` and read the output. Anything you did not intend to commit must be either resolved (stashed/reset/disclosed) or excluded from the stage.
2. Stage with explicit paths only:
   ```bash
   git add CLAUDE/skills/foo.md teams/orchestrator.md .klodTalk/instincts.md
   ```
3. Verify what is staged: `git diff --cached --stat`. If the staged file list exceeds the explicit list, something is wrong — investigate.
4. Commit only after the staged-file-stat matches expectation.
5. In `coder_output.txt`, list every file the commit touches (the "Files Changed" section). If any pre-existing working-tree drift was unavoidably included, name it under "Deviations" so the reviewer is not surprised.

## Related
- `orchestrator-step-edits` — guards `teams/orchestrator.md` against accidental renumbering.
- `placeholder-guard` — pre-commit content scan; complementary to this skill's pre-commit *staging* check.
