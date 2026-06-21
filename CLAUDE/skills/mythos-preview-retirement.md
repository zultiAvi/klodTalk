---
skill_name: mythos-preview-retirement
triggers:
  - Considering adding claude-mythos-preview to availableModels or any role/alias target
  - Diagnosing API errors from a claude-mythos-preview model selection after 2026-06-30
  - Searching for a migration target away from claude-mythos-preview
summary: "`claude-mythos-preview` retires 2026-06-30 — hard API error after that date; there is NO general-access successor (`claude-mythos-5` is export-control SUSPENDED, Project Glasswing-only). Never add `claude-mythos-preview` to availableModels or role files."
---

# Skill: claude-mythos-preview Retirement (2026-06-30)

## Quick Reference
- **Retirement date: 2026-06-30** (absolute). On and after that date, any API call resolving to `claude-mythos-preview` returns an error.
- **No general-access successor.** The only stated successor, `claude-mythos-5`, is export-control **SUSPENDED** (2026-06-12) and was Project Glasswing-only — it is NOT a valid migration target.
- **Rule:** never add `claude-mythos-preview` to `/workspace/.claude/settings.json` `availableModels`, `fallbackModel`, or any role/alias target.
- KlodTalk's supported models are unchanged: `opus` -> `claude-opus-4-8`, `sonnet` -> `claude-sonnet-4-6`, `haiku` -> `claude-haiku-4-5-20251001`.
- `claude-mythos-preview` is currently **absent** from all KlodTalk config and role files (grep-confirmed 2026-06-21) — keep it that way.

## When to Use
Apply this whenever a scout, evaluator, or coder is tempted to add `claude-mythos-preview` to a config, or when diagnosing why a request to that ID started failing after June 30, 2026. It documents the dead-end successor situation so no agent wastes time hunting for a valid migration path.

## Instructions
- **Do NOT add `claude-mythos-preview`** to `availableModels`. With `enforceAvailableModels: true` (CLI >= 2.1.174), whitelisting a retired ID does not enable it — after 2026-06-30 it just guarantees a hard API failure the moment an alias or config string resolves to it (see `enforce-available-models.md`).
- **Do NOT use it** as a `fallbackModel` entry, a role/alias target, or a default model.
- **Do NOT migrate to `claude-mythos-5`** as the "successor": it is export-control suspended and Glasswing-only — picking it just trades one guaranteed failure for another (see `model-suspension-fable-mythos-5.md`).
- What breaks post-2026-06-30: any container session, role, or `/config model=...` override that resolves to `claude-mythos-preview` fails at request time. Because KlodTalk runs unattended nightly, a retired ID in config is a guaranteed mid-pipeline failure rather than a graceful fallback.
- Settings shape to KEEP (the ID is simply never present):

```json
{
  "enforceAvailableModels": true,
  "availableModels": [
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001"
  ]
}
```

## Cross-References
- `model-suspension-fable-mythos-5.md` — why `claude-mythos-5` (the only stated successor) is export-control suspended and also unusable.
- `enforce-available-models.md` — the allowlist-enforcement layer that turns a retired/suspended ID into an early hard block.
- `model-version-hygiene.md` — current vs retired/suspended model IDs and alias resolution.

## Source Attribution
- Anthropic model deprecations page — https://platform.claude.com/docs/en/docs/about-claude/model-deprecations (docs.anthropic.com, retrieved 2026-06-21): `claude-mythos-preview` retirement date of 2026-06-30; no general-access successor (`claude-mythos-5` export-control suspended, Project Glasswing-only). Official Anthropic documentation, no star count applicable.
