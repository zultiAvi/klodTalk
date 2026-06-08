---
skill_name: operator-fallback-model
triggers:
  - Agents/orchestrator stalling or erroring when the primary model (Opus) is overloaded
  - Adding graceful-degradation to unattended pipelines (nightly_scout, optimizer, tdd)
  - Editing .claude/settings.json operator settings for the agent containers
summary: Add a `fallbackModel` list to .claude/settings.json so agents fall back (opus to sonnet to haiku) on overload instead of stalling (Claude Code v2.1.166+).
---

# Skill: fallbackModel Operator Setting for Graceful Degradation

## Quick Reference
- Add a top-level `fallbackModel` array to `/workspace/.claude/settings.json`.
- Up to 3 models, tried in order when the primary is overloaded/unavailable. Requires Claude Code v2.1.166+.
- Use CURRENT non-retiring model IDs only (e.g. `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`). Never list `*-20250514` (retires 2026-06-15).

## When to Use
When the orchestrator or per-role agents (especially the Opus-backed Coder/orchestrator in unattended nightly pipelines) can silently stall on Opus overload, and you want them to degrade and finish rather than error mid-run.

## Why It Matters
KlodTalk has no graceful-degradation path by default; an overloaded primary model surfaces as a stalled or failed pipeline with no human watching. `fallbackModel` is the operator-level safety net.

## Instructions
1. Edit `/workspace/.claude/settings.json` (the operator-level file `run_agent.py` mounts into containers — NOT `~/.claude/settings.json`, which `_setup_agent_hooks()` overwrites).
2. Add a top-level key alongside existing keys; preserve the full `hooks` block and all other keys verbatim:
   ```json
   "fallbackModel": ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
   ```
3. Validate JSON: `python3 -m json.tool /workspace/.claude/settings.json`.
4. No Python changes are needed — the setting is consumed by the CLI runtime, not by KlodTalk code.
5. Document the key in `config/CLAUDE.md` for discoverability.

## Notes
- This is the settings-file equivalent of the `--fallback-model` CLI flag; the flag also applies to interactive sessions since v2.1.166.
- Source: Claude Code CHANGELOG v2.1.166 (https://code.claude.com/docs/en/changelog).

## Related
- `model-version-hygiene` — keep model IDs current; fallback IDs must also be non-retiring.
- `three-tier-model-routing` — per-role model selection (opus/sonnet/haiku).
