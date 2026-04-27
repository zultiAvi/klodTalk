---
skill_name: placeholder-guard
triggers:
  - Reviewing code changes before committing
  - Catching incomplete implementations or forgotten TODOs
  - Running pre-commit self-checks on changed files
summary: Scan changed files for TODO/FIXME/HACK/XXX, empty bodies, stub returns, and placeholder values.
---

# Skill: Stub and Placeholder Detection

## Quick Reference
- Markers to find: `TODO`, `FIXME`, `HACK`, `XXX`, `PLACEHOLDER`
- Stubs: empty bodies, bare `pass`, `NotImplementedError`, `...` as body
- Placeholders: `"example.com"`, `"changeme"`, `"your-api-key-here"`, `"lorem ipsum"`, `password123`

## When to Use
When reviewing code changes or before committing, to catch incomplete implementations, placeholder values, and forgotten TODOs.

## Instructions

### For the Coder Role
Before every commit, run a self-check on all changed files:
1. Search for marker comments: `TODO`, `FIXME`, `HACK`, `XXX`, `PLACEHOLDER`
2. Look for empty or stub implementations: empty function bodies, bare `pass`, `NotImplementedError`, `...` as body
3. Check for placeholder values: `"example.com"`, `"changeme"`, `"your-api-key-here"`, `"lorem ipsum"`, `password123`
4. Flag commented-out code blocks (3+ consecutive lines)
5. Fix all findings before committing, or add an explicit justification comment if a TODO must remain

### For the Reviewer Role
Under "Must-check", the reviewer should verify:
- No new `TODO`/`FIXME`/`HACK`/`XXX`/`PLACEHOLDER` markers were introduced
- No empty or stub function bodies exist where real logic is expected
- No placeholder or dummy values are present
- Commented-out code blocks are flagged as `WARNING`
- Stub return values (`None`, `null`, `0`, `""`, `[]`, `{}`) without logic are flagged when the plan describes real behavior

Each finding is a `BLOCKER` unless it existed before the change.

### Key Files
- `teams/roles/coder.md` — "Pre-Commit Self-Check" section
- `teams/roles/reviewer.md` — "Stub and Placeholder Detection" subsection under Must-check

### Source
Inspired by carlrannaberg/claudekit (github.com/carlrannaberg/claudekit, ~648 stars).
