---
skill_name: three-tier-model-routing
triggers:
  - Authoring a new team `.md` and choosing models for each member
  - Auditing an existing team for over- or under-provisioned model tiers
  - Reviewing a PR that adds/changes model shorthands in `teams/teams/*.md`
summary: Pick `opus` for roles whose output is committed/shipped, `sonnet` for planning/review/evaluation, `haiku` for pure I/O -- applied consistently across all KlodTalk teams.
---

# Skill: Three-Tier Model Routing

## Instructions

Apply this routing policy to every new team definition in `teams/teams/*.md`, and audit existing teams (~20) for cost/quality mismatches.

| Tier | Shorthand | Use For |
|------|-----------|---------|
| Critical | `opus` | Roles whose output is committed/shipped (Coder, security Fixer, final Refactorer). |
| Complex | `sonnet` | Planning, reviewing, evaluating, summarising -- reasoning-heavy, no direct write. |
| Utility | `haiku` | Pure I/O: scouts that just write a markdown file, broadcasters, status reporters. |

**Decision table (KlodTalk roles):**
| Role Type | Tier | Rationale |
|-----------|------|-----------|
| Coder, Fixer, Refactorer | `opus` | Output committed to a branch. |
| Planner, Reviewer, Evaluator | `sonnet` | Complex reasoning, no write to repo. |
| Scout, Broadcaster, Doc-Only | `haiku` | Markdown write only, no code reasoning. |

**Anti-patterns:**
- Haiku as the sole Reviewer -- under-provisions bug detection.
- Opus on a Scout that only writes a finding list -- wasteful.
- Mixing tiers within the same review loop without justification -- makes findings non-reproducible.

**Cost / quality notes:** Opus is roughly 5x the per-token cost of Sonnet; reserve it for roles whose output you would otherwise re-run by hand. See `model-version-hygiene.md` for active model IDs.

**Where to check:** `teams/teams/*.md` member tables -- column `model` should match this policy. `teams/run_claude_team.sh` pins the orchestrator itself to `opus` (correct: orchestration is critical).

## Source
wshobson/agents -- https://github.com/wshobson/agents (~35,500 stars). Three-tier routing policy extracted from their orchestrator templates.
