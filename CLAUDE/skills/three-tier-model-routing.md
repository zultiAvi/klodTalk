---
skill_name: three-tier-model-routing
triggers:
  - Authoring a new team `.md` and choosing models for each member
  - Auditing an existing team for over- or under-provisioned model tiers
  - Reviewing a PR that adds/changes model shorthands in `teams/teams/*.md`
summary: Pick `opus` for roles whose output is committed/shipped, `sonnet` for planning/review/evaluation, `haiku` for pure I/O — applied consistently across all KlodTalk teams.
---

# Skill: Three-Tier Model Routing

## Quick Reference
| Tier | Shorthand | Use For |
|------|-----------|---------|
| Critical | `opus` | Roles whose output is committed, shipped, or hard to undo (Coder, security Fixer, final Refactorer). |
| Complex | `sonnet` | Planning, reviewing, evaluating, summarising — reasoning-heavy but no direct write. |
| Utility | `haiku` | Pure I/O: scouts that just write a markdown file, broadcasters, status reporters. |

## When to Use
- Every new team definition in `teams/teams/*.md`.
- Auditing existing teams (currently ~20) for cost/quality mismatches.

## Decision Table (KlodTalk Roles)
| Role Type | Tier | Rationale |
|-----------|------|-----------|
| Coder, Fixer, Refactorer | `opus` | Output is committed to a branch. |
| Planner, Reviewer, Evaluator | `sonnet` | Complex reasoning, no write to repo. |
| Scout, Broadcaster, Doc-Only | `haiku` | Markdown write only, no code reasoning. |

## Anti-Patterns
- Haiku as the sole Reviewer — under-provisions bug detection.
- Opus on a Scout that only writes a finding list — wasteful.
- Mixing tiers within the same review loop without justification — makes findings non-reproducible.

## Cost / Quality Notes
- See `model-version-hygiene.md` for the active model IDs each shorthand resolves to.
- Opus is roughly 5x the per-token cost of Sonnet; reserve it for roles whose output you would otherwise re-run by hand.

## Where to Check
- `teams/teams/*.md` member tables — column `model` should match this policy.
- `teams/run_claude_team.sh` — orchestrator launcher pins the orchestrator itself to `opus` (correct: orchestration is critical).

## Source
wshobson/agents — https://github.com/wshobson/agents (~35,500 stars). Three-tier routing policy extracted from their orchestrator templates.
