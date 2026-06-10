---
skill_name: model-version-hygiene
triggers:
  - Updating model references in team definitions or config files
  - Diagnosing API errors from retired model identifiers
  - Migrating from budget_tokens to the effort parameter
summary: Current and retired model IDs, shorthand resolution, and effort parameter reference.
---

# Skill: Model Version Hygiene

## Quick Reference
- Wired shorthands (KlodTalk resolution): `opus` -> `claude-opus-4-8`, `sonnet` -> `claude-sonnet-4-6`, `haiku` -> `claude-haiku-4-5-20251001`
- New top tier (June 9 2026): `claude-fable-5` (most capable widely-released model) and `claude-mythos-5` (limited availability, Project Glasswing). NOT wired as KlodTalk shorthands — see "Fable 5 / Mythos 5" below.
- Effort parameter (GA): `low`, `medium`, `high` (replaces deprecated `budget_tokens`)
- Deprecation docs: https://docs.anthropic.com/en/docs/about-claude/model-deprecations

## When to Use
When updating model references in team definitions, config files, or server code. When diagnosing API errors that may be caused by retired model identifiers. When migrating from `budget_tokens` to the `effort` parameter.

## Active Models (as of June 2026)

| Shorthand | Full Model ID | Notes |
|-----------|---------------|-------|
| `opus` | `claude-opus-4-8` | Most capable Opus-tier; default orchestrator model |
| `sonnet` | `claude-sonnet-4-6` | Balanced capability and speed |
| `haiku` | `claude-haiku-4-5-20251001` | Fastest and cheapest (alias `claude-haiku-4-5`) |

Note: `claude-opus-4-8` and `claude-sonnet-4-6` are dateless pinned IDs (4.6-generation
naming) — they are snapshots, not evergreen pointers. `claude-haiku-4-5-20251001` is the
full dated ID; `claude-haiku-4-5` is its convenience alias. KlodTalk uses the full dated
form for haiku.

## Fable 5 / Mythos 5 (released June 9 2026)

| Model | Full Model ID | Availability |
|-------|---------------|--------------|
| Claude Fable 5 | `claude-fable-5` | GA — most capable widely-released model (above Opus-tier) |
| Claude Mythos 5 | `claude-mythos-5` | Limited availability (Project Glasswing, invitation-only) |
| Claude Mythos Preview | `claude-mythos-preview` | Invitation-only research preview |

These are NOT wired into KlodTalk's `opus`/`sonnet`/`haiku` resolution (`server/server.py`
`CURRENT_MODELS`, `teams/run_claude_team.sh`). The `opus` shorthand still resolves to
Opus 4.8, not Fable 5. To use Fable 5, reference the full ID `claude-fable-5` directly.
Wiring `fable` as a new shorthand would also require updating the nightly model-check
validation regex in `server/server.py:_query_latest_model` (currently
`^claude-(opus|sonnet|haiku)-...`) and confirming `fable` is an accepted CLI `--model` alias.

## Legacy Models (still available — prefer current)

| Model ID | Status | Prefer |
|----------|--------|--------|
| `claude-opus-4-7` | Legacy | `claude-opus-4-8` |
| `claude-opus-4-6` | Legacy | `claude-opus-4-8` |
| `claude-sonnet-4-5-20250929` | Legacy | `claude-sonnet-4-6` |
| `claude-opus-4-5-20251101` | Legacy | `claude-opus-4-8` |

## Retired / Deprecated Models (Do Not Use)

| Model ID | Status | Replacement |
|----------|--------|-------------|
| `claude-3-haiku-20240307` | RETIRED (March 2026) | `claude-haiku-4-5-20251001` |
| `claude-3-7-sonnet` | RETIRED | `claude-sonnet-4-6` |
| `claude-3-5-haiku` | RETIRED | `claude-haiku-4-5-20251001` |
| `claude-sonnet-4-20250514` | Deprecated — retiring June 15, 2026 | `claude-sonnet-4-6` |
| `claude-opus-4-20250514` | Deprecated — retiring June 15, 2026 | `claude-opus-4-8` |
| `claude-opus-4-1-20250805` | Deprecated — retiring Aug 5, 2026 | `claude-opus-4-8` |

## Effort Parameter (Replaces budget_tokens)

The `effort` parameter is GA as of April 2026, replacing the deprecated `budget_tokens`:

| Value | Behavior |
|-------|----------|
| `low` | Minimal thinking, fastest responses |
| `medium` | Balanced (default if omitted) |
| `high` | Maximum thinking, most thorough |

If you find `budget_tokens` in any `.py` file, replace it with the appropriate `effort` level.

Note: On Claude Opus 4.8 the `effort` parameter defaults to `high` on all surfaces
(Claude API and Claude Code). Set `effort` explicitly to use a different level.

## Where to Check

- `config/server_config.yaml` — model shorthand resolution is documented in comments
- `teams/teams/*.md` — member tables use shorthands (`opus`, `sonnet`, `haiku`)
- `teams/run_claude_team.sh` — model mapping in the orchestrator launcher
- `server/*.py` — any direct API calls with model parameters

## Checking for Deprecations

1. Search for retired/deprecated model strings: `grep -rn "claude-3-7-sonnet\|claude-3-5-haiku\|claude-3-haiku-20240307\|claude-sonnet-4-20250514\|claude-opus-4-20250514\|claude-opus-4-1-20250805"`
2. Search for budget_tokens: `grep -rn "budget_tokens" server/`
3. Check Anthropic deprecation page: https://docs.anthropic.com/en/docs/about-claude/model-deprecations
