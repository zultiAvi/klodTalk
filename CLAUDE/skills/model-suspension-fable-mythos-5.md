---
skill_name: model-suspension-fable-mythos-5
triggers:
  - Considering adding claude-fable-5 or claude-mythos-5 to a config or allowlist
  - Diagnosing API failures from a fable-5 / mythos-5 model selection
  - Choosing a model/alias target for a KlodTalk role
summary: "claude-fable-5 and claude-mythos-5 are SUSPENDED (export control); never add them to availableModels or use as a role/alias target."
---

# Skill: Fable 5 / Mythos 5 Export-Control Suspension

## What Happened

- `claude-fable-5` and `claude-mythos-5` **launched ~2026-06-09**.
- Both were **SUSPENDED ~2026-06-12** by a US government export-control
  directive. They are no longer selectable; any request against either ID
  fails.

## Rules

- **Do NOT** add `claude-fable-5` or `claude-mythos-5` to
  `/workspace/.claude/settings.json` `availableModels`. With
  `enforceAvailableModels: true` (CLI >= 2.1.174), whitelisting a suspended ID
  does not enable it — it just guarantees a hard API failure the moment an alias
  or config string resolves to it (see `enforce-available-models.md`).
- **Do NOT** use either ID as a role/alias target, a `fallbackModel` entry, or a
  default model.
- KlodTalk's supported models remain unchanged:
  - `opus`   -> `claude-opus-4-8`
  - `sonnet` -> `claude-sonnet-4-6`
  - `haiku`  -> `claude-haiku-4-5-20251001`

## Why This Matters Here

This is **why the nightly of 2026-06-15 removed `claude-fable-5` from the
`availableModels` allowlist** in `.claude/settings.json`. A prior nightly had
whitelisted Fable 5 while it was briefly live; once it was suspended, leaving it
in the allowlist meant any selection of it was a guaranteed mid-pipeline
failure. `claude-mythos-5` was never added (it had been Glasswing-only) and must
stay out as well.

## Related

- `model-version-hygiene.md` — current vs retired/suspended model IDs and alias
  resolution. Its "Fable 5 Breaking Constraints" section is now historical only.
- `enforce-available-models.md` — the allowlist enforcement layer that turns a
  suspended/retired ID into an early hard block.

## Source

- website_scout finding (Anthropic news / Claude Code release notes,
  2026-06-09..2026-06-12): Fable 5 / Mythos 5 launch (~2026-06-09) and
  subsequent export-control suspension (~2026-06-12).
