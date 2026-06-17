---
skill_name: safe-mode-config-bisect
triggers:
  - A containerized role misbehaves and you can't tell if KlodTalk config or the CLI is at fault
  - Bisecting whether a failure comes from hooks/skills/settings overrides vs the bundled CLI
  - Debugging a broken role/hook config in a Docker agent container
summary: "Launch a role container with CLAUDE_CODE_SAFE_MODE=1 (or --safe-mode) to start with ALL customizations disabled (hooks, skills, settings overrides) and isolate whether a failure is a KlodTalk customization or the bundled CLI. Diagnostic-only; no runtime change."
---

# Skill: `--safe-mode` / `CLAUDE_CODE_SAFE_MODE` Config-Bisect

## Quick Reference
- `CLAUDE_CODE_SAFE_MODE=1` (env var) or `--safe-mode` (flag) starts a Claude Code session
  with **all customizations disabled**: hooks, skills, and `settings.json` overrides.
- Available in Claude Code ~v2.1.172–2.1.176 (within KlodTalk's 2.1.178 floor — see
  `required-minimum-version-pin.md`).
- `/cd <path>` moves a running session's cwd **without rebuilding the prompt cache** —
  handy when bisecting across subtrees mid-session.
- **Diagnostic aid only.** Do NOT bake it into the runtime — no `Dockerfile.agent` or
  server launch-code edits.

## When / Why to Use
KlodTalk layers a lot on top of the bundled CLI: `.claude/settings.json` hooks (installed
by `server/run_agent.py`), ~80 skills in `CLAUDE/skills/`, and role frontmatter. When a
containerized role misbehaves it is hard to tell whether the fault is a KlodTalk
customization or the CLI itself. Safe-mode is the canonical "bisect KlodTalk-config vs
upstream" lever:
1. Reproduce the failure normally (all customizations on).
2. Re-run the same prompt with safe-mode on. If the failure **disappears**, it's a
   KlodTalk customization (hook/skill/setting). If it **persists**, it's the bundled CLI
   or the prompt/model itself.
3. Re-enable customizations one layer at a time to pinpoint the culprit.

## Container-Friendly Form
Prefer the **env-var** form `CLAUDE_CODE_SAFE_MODE=1` for one-off container debugging — pass
it via `docker exec -e CLAUDE_CODE_SAFE_MODE=1 ...` for the diagnostic run only. This
mirrors how other `CLAUDE_CODE_*` vars are forwarded (see `_claude_env()` in
`server/run_agent.py`, e.g. `CLAUDE_CODE_CONTEXT_COMPACTION`). The `--safe-mode` flag works
too but the env var is cleaner for transient, per-exec isolation without touching launch
code.

## Cross-References
- `docker-claude-stability.md` — pinning the CLI version / suppressing auto-updates; the
  broader container debug story this complements.
- `required-minimum-version-pin.md` — the version floor that guarantees safe-mode is present.

## Source
- anthropics/claude-code changelog ~v2.1.172–2.1.176, via releasebot.io (releasebot.io) —
  https://releasebot.io/updates/anthropic/claude-code
