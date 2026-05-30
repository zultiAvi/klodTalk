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
- Shorthands: `opus` -> `claude-opus-4-8`, `sonnet` -> `claude-sonnet-4-6`, `haiku` -> `claude-haiku-4-5-20251001`
- Effort parameter (GA): `low`, `medium`, `high` (replaces deprecated `budget_tokens`)
- Sampling param restriction: `temperature`, `top_p`, `top_k` non-default values return HTTP 400 on Opus 4.7+
- Deprecation docs: https://docs.anthropic.com/en/docs/about-claude/model-deprecations

## When to Use
When updating model references in team definitions, config files, or server code. When diagnosing API errors that may be caused by retired model identifiers. When migrating from `budget_tokens` to the `effort` parameter.

## Active Models (as of May 2026)

| Shorthand | Full Model ID | Notes |
|-----------|---------------|-------|
| `opus` | `claude-opus-4-8` | Most capable, highest cost (launched May 28 2026) |
| `sonnet` | `claude-sonnet-4-6` | Balanced capability and speed |
| `haiku` | `claude-haiku-4-5-20251001` | Fastest and cheapest |

## Superseded Models (Still Working, Migrate Soon)

| Model ID | Status | Replacement |
|----------|--------|-------------|
| `claude-opus-4-7` | Superseded May 28 2026 by `claude-opus-4-8` | `claude-opus-4-8` |

## Retired Models (Do Not Use)

| Model ID | Status | Replacement |
|----------|--------|-------------|
| `claude-3-haiku-20240307` | RETIRED (March 2026) | `claude-haiku-4-5-20251001` |
| `claude-sonnet-4-20250514` | **URGENT** — retires June 15, 2026 (16 days) | `claude-sonnet-4-6` |
| `claude-opus-4-20250514` | **URGENT** — retires June 15, 2026 (16 days) | `claude-opus-4-8` |
| `claude-3-7-sonnet` | RETIRED | `claude-sonnet-4-6` |
| `claude-3-5-haiku` | RETIRED | `claude-haiku-4-5-20251001` |

> **URGENT — June 15, 2026 retirement (16 days from 2026-05-30):**
> Both `claude-sonnet-4-20250514` and `claude-opus-4-20250514` hard-retire on
> June 15, 2026. Any role, team definition, or server call still pinned to
> these IDs will start returning API errors that day. Audit and migrate now.

## Sampling Param Restriction (Opus 4.7+)

On `claude-opus-4-7` and `claude-opus-4-8`, setting any of `temperature`,
`top_p`, or `top_k` to a non-default value returns **HTTP 400**. Roles or
config files that explicitly set these parameters will break silently on
upgrade — the failure surfaces as an API error mid-pipeline, not at config
load.

- Remove `temperature`, `top_p`, and `top_k` from any Opus 4.7/4.8 call site.
- For controlled variation, use the `effort` parameter instead.
- Sonnet and Haiku models still accept these parameters normally.

## Effort Parameter (Replaces budget_tokens)

The `effort` parameter is GA as of April 2026, replacing the deprecated `budget_tokens`:

| Value | Behavior |
|-------|----------|
| `low` | Minimal thinking, fastest responses |
| `medium` | Balanced (default if omitted) |
| `high` | Maximum thinking, most thorough |

If you find `budget_tokens` in any `.py` file, replace it with the appropriate `effort` level.

## Where to Check

- `config/server_config.yaml` — model shorthand resolution is documented in comments
- `teams/teams/*.md` — member tables use shorthands (`opus`, `sonnet`, `haiku`)
- `teams/run_claude_team.sh` — model mapping in the orchestrator launcher
- `server/*.py` — any direct API calls with model parameters

## Checking for Deprecations

1. Search for retired model strings: `grep -rn "claude-3-7-sonnet\|claude-3-5-haiku\|claude-3-haiku-20240307\|claude-sonnet-4-20250514\|claude-opus-4-20250514"`
2. Search for superseded Opus 4.7: `grep -rn "claude-opus-4-7"`
3. Search for budget_tokens: `grep -rn "budget_tokens" server/`
4. Search for forbidden sampling params on Opus calls: `grep -rn "temperature\|top_p\|top_k" server/`
5. Check Anthropic deprecation page: https://docs.anthropic.com/en/docs/about-claude/model-deprecations
