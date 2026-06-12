---
skill_name: operator-fallback-model
triggers:
  - Agents/orchestrator stalling or erroring when the primary model (Opus) is overloaded
  - Adding graceful-degradation to unattended pipelines (nightly_scout, optimizer, tdd)
  - Editing .claude/settings.json operator settings for the agent containers
summary: Add a `fallbackModel` list to .claude/settings.json so agents fall back (sonnet to haiku) on overload instead of stalling (Claude Code v2.1.166+); the list holds models tried AFTER the primary, so do not include the opus primary in it.
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
   Slot order matters: the primary model is tried first, then each entry in the
   array is tried in order on overload/unavailability. Up to 3 entries are
   supported (Claude Code v2.1.166+).
   - **Why no `claude-opus-4-8` in the list:** the array holds models tried
     *after* the primary on overload. KlodTalk's safety-net roles are
     opus-primary (orchestrator, coder), so listing opus as the first fallback
     would just retry the already-overloaded primary. The 2-entry sonnet→haiku
     chain is the better *universal* fallback — it degrades to genuinely lighter
     models and works unchanged for opus- and sonnet-primary roles alike. Keep
     this list and the live `/workspace/.claude/settings.json` value identical so
     they don't drift.
3. Validate JSON: `python3 -m json.tool /workspace/.claude/settings.json`.
4. No Python changes are needed — the setting is consumed by the CLI runtime, not by KlodTalk code.
5. Document the key in `config/CLAUDE.md` for discoverability.

## Disabling Adaptive Thinking (MAX_THINKING_TOKENS=0)

`MAX_THINKING_TOKENS=0` (env var, available v2.1.166+) disables adaptive
thinking on models that think by default (e.g. Fable 5, Opus 4.8). Use it for
**latency/cost-sensitive roles that are pure extraction, formatting, or review**
and do not need deep reasoning — e.g. `website_scout`, `reviewer`. Roles that
plan, design, or debug should keep thinking on.

Set it as a Docker container env var for the role: KlodTalk injects per-role env
in `server/run_agent.py`, so add the variable to that role's environment there
rather than globally. Note: on Fable 5, attempting to disable thinking via the
API (`thinking: {"type":"disabled"}`) returns HTTP 400 — `MAX_THINKING_TOKENS=0`
is the supported way to suppress it.

## Notes
- This is the settings-file equivalent of the `--fallback-model` CLI flag; the flag also applies to interactive sessions since v2.1.166.
- Source: Claude Code CHANGELOG v2.1.166 (https://code.claude.com/docs/en/changelog).

## Related
- `model-version-hygiene` — keep model IDs current; fallback IDs must also be non-retiring.
- `three-tier-model-routing` — per-role model selection (opus/sonnet/haiku).
- `disallowed-tools-frontmatter` — glob `"*"` in deny rules blocks ALL tools for that rule (v2.1.166+).
