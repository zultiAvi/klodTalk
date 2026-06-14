---
skill_name: enforce-available-models
triggers:
  - Locking the agent containers to an allowlist of non-retired model IDs
  - Preventing a model shorthand/alias from resolving to a retired or unintended model
  - Hardening KlodTalk against a mid-pipeline API failure the day a model retires
summary: "Claude Code (>= 2.1.174) managed settings `enforceAvailableModels: true` + `availableModels: [...]` constrain the Default model to an allowlist and block alias redirects to non-listed models — a harness-level hard block on retired model IDs, enforced instead of relying on do-not-use comments. Doc/config only — no server logic."
---

# Skill: enforceAvailableModels Allowlist

## Quick Reference
- Keys: `enforceAvailableModels` (bool) + `availableModels` (string[]) — managed settings, Claude Code **>= 2.1.174**.
- Effect: with `enforceAvailableModels: true`, the CLI restricts the Default model to the `availableModels` allowlist and **blocks an alias/shorthand from redirecting to a model not on the list**. A selection outside the allowlist is refused at the CLI layer, not silently downgraded.
- KlodTalk allowlist (matches the shorthands in `model-version-hygiene.md`):
  ```json
  "enforceAvailableModels": true,
  "availableModels": [
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-fable-5"
  ]
  ```
- Location: workspace-level `/workspace/.claude/settings.json` (see `hook-settings-location.md`). Settings only — do NOT touch server logic, auth, or `Dockerfile.agent`.

## When to Use
- KlodTalk selects models via shorthand aliases (`opus`/`sonnet`/`haiku`, resolved in
  `teams/run_claude_team.sh`). If an alias or a stale config string ever resolves
  to a retired ID (e.g. `claude-opus-4-20250514` / `claude-sonnet-4-20250514`,
  which hard-retire 2026-06-15), the failure surfaces as an API error mid-pipeline.
- `enforceAvailableModels` turns that class of failure into an **early, harness-level
  hard block**: a model outside the allowlist cannot be selected at all. This is the
  enforcement layer that complements the *documentation* layer (`model-version-hygiene.md`'s
  "Retired Models — Do Not Use" table) and the *version* layer
  (`required-minimum-version-pin.md`).

## Background
As of Claude Code 2.1.174, managed settings support an `availableModels` allowlist
gated by `enforceAvailableModels`. When enforcement is on:
- The **Default** model must be one of `availableModels`.
- An **alias redirect** (a shorthand or `--model` that would resolve to a model
  not on the list) is blocked rather than honored.

This is purely a settings-file change. Older CLIs that predate 2.1.174 ignore the
unknown keys (no-op), so the allowlist degrades gracefully — but because KlodTalk
also pins `requiredMinimumVersion: 2.1.176` (see `required-minimum-version-pin.md`),
the runtime is guaranteed to honor enforcement.

## Settings Snippet
Add to `/workspace/.claude/settings.json` alongside the version pin:

```json
{
  "requiredMinimumVersion": "2.1.176",
  "enforceAvailableModels": true,
  "availableModels": [
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-fable-5"
  ]
}
```

## Keep In Sync
Whenever a new model is adopted (or an old one retires) in `model-version-hygiene.md`,
update `availableModels` to match the "Active Models" table. The allowlist and the
hygiene doc must not drift apart — a model present in one but absent from the other
is a latent block (a valid model refused) or a latent gap (a retired model still
selectable).

## Cross-References
- `model-version-hygiene.md` — the canonical Active/Retired model table this allowlist mirrors (its "Where to Check" section links back here as the enforcement layer).
- `required-minimum-version-pin.md` — the `requiredMinimumVersion: 2.1.176` floor that guarantees this enforcement is honored.
- `hook-settings-location.md` — why this goes in the workspace-level settings file.

## Source
- Claude Code CHANGELOG v2.1.174 / v2.1.176 (`enforceAvailableModels`, `availableModels`) —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
