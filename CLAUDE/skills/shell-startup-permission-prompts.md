---
skill_name: shell-startup-permission-prompts
triggers:
  - A nightly/orchestrator container run stalls waiting on a permission prompt
  - A role drops `--dangerously-skip-permissions` or uses `acceptEdits` mode
  - Adding per-agent OTEL telemetry labels for multi-agent observability
summary: "Claude Code 2.1.160 prompts before sourcing shell startup files (`.zshenv`, `.zlogin`, `.bash_login`) and for build-tool configs in `acceptEdits`; KlodTalk's `--dangerously-skip-permissions` launches bypass it, but pre-approve the rules in workspace `settings.json` so behavior is explicit, not flag-dependent. 2.1.161 adds `OTEL_RESOURCE_ATTRIBUTES` per-agent labels."
---

# Skill: Shell-Startup Permission Prompts (CLI 2.1.160/2.1.161)

## Quick Reference
- 2.1.160: Claude Code now PROMPTS before sourcing shell startup files (`.zshenv`, `.zlogin`, `.bash_login`) and for build-tool configs when in `acceptEdits` mode. `grep` now satisfies read-before-edit.
- 2.1.161: adds `OTEL_RESOURCE_ATTRIBUTES` labels for per-agent telemetry, Linux clipboard via `wl-copy`/`xclip`, and fixes org-managed permission rules.
- These features need the 2.1.160/161 floor — see `required-minimum-version-pin.md`.
- KlodTalk's Bash tool initializes from the user's profile, so a new prompt could stall an unattended container run.

## Why KlodTalk Is (Mostly) Safe Today
KlodTalk launches Claude with `--dangerously-skip-permissions`, which suppresses these prompts:
- `server/run_agent.sh:156`, `:214`, `:460`
- `server/server.py:2570`, `:2746`
- `server/run_agent.py:289`
A run using these flags will NOT stall on the new startup-file prompt.

## The Residual Risk
- Any role/path that REMOVES `--dangerously-skip-permissions` (or switches to `acceptEdits` mode) regains the stall risk: a non-interactive container has no human to answer the prompt, so the run hangs until timeout.
- Flag-dependence is fragile — a future refactor could silently reintroduce a stall.

## Safe Mitigation (doc/config only — no code edits)
Pre-approve the relevant permission rules in workspace-level `/workspace/.claude/settings.json` so the behavior is explicit rather than flag-dependent (see `hook-settings-location.md`). This makes the run survive even if a role drops the skip-permissions flag.

## Per-Agent Telemetry (2.1.161)
Set `OTEL_RESOURCE_ATTRIBUTES` (e.g. `role=coder,session=<sid>`) per agent to tag telemetry by role/session — complements `multi-agent-hook-observability.md`. This is an env var, not role frontmatter (frontmatter only forwards `mcpServers`/`disallowedTools` — instinct #7/#16).

## Cross-References
- `required-minimum-version-pin.md` — pin the 2.1.160/161 floor so these behaviors are guaranteed.
- `hook-settings-location.md` — where workspace settings live.
- `multi-agent-hook-observability.md` — the OTEL labeling companion.

## Source
Claude Code CLI 2.1.160/2.1.161 — shell-startup-file permission prompts & parallel-tool independence — https://code.claude.com/docs/en/changelog (code.claude.com changelog, 2026-06-02).
