---
skill_name: native-subagent-prompt-drift
triggers:
  - The pinned Claude Code CLI floor is bumped in required-minimum-version-pin.md
  - A KlodTalk role prompt seems to conflict with native sub-agent behavior
  - Auditing teams/roles/ against the harness's built-in Plan/Explore/Task prompts
summary: "Use the Piebald-AI tracker to fetch the native Plan/Explore/Task sub-agent prompts for the pinned CLI floor and diff them against base.md + planner/coder/reviewer to catch silent drift whenever the floor moves."
---

# Skill: Native Sub-Agent Prompt-Drift Detection

## Quick Reference
- Tracker: Piebald-AI/claude-code-system-prompts — https://github.com/Piebald-AI/claude-code-system-prompts (~11k stars)
- Tracks every native sub-agent prompt (Plan / Explore / Task) + all built-in tool descriptions, per CLI release (latest tracked v2.1.173).
- KlodTalk roles run AS Claude Code sub-agents, so the native prompt is the baseline our role text layers on top of.

## When to Use
Whenever the CLI floor is bumped in `required-minimum-version-pin.md`, or when a role prompt appears to fight the harness (redundant or contradictory tool-use guidance).

## Instructions
1. Find the pinned floor (e.g. v2.1.172) in `required-minimum-version-pin.md`.
2. From the tracker, open the matching tagged version and fetch the Plan, Explore, and Task agent prompts (and any changed built-in tool descriptions).
3. Diff against KlodTalk role text:
   - Plan agent ↔ `teams/roles/planner.md`
   - Task agent (general implementation/tool-use framing) ↔ `teams/roles/coder.md` + shared `teams/roles/base.md`
   - Explore/read-only framing ↔ `teams/roles/reviewer.md` and any read-only role
4. For each section, classify: **redundant** (native already says it — consider trimming), **consistent** (leave), or **conflicting** (native and role disagree).
5. On a conflict: prefer adjusting the KlodTalk role to defer to the native baseline rather than restating it; if the role intentionally overrides, add a one-line comment in the role file saying so. Record the finding in this skill's notes below.

## Audit Notes
- v2.1.172/173 baseline: no hard conflicts found between native Task/Plan prompts and `base.md`/coder/planner; main overlap is generic tool-use phrasing in coder (consistent, left as-is). Re-run this audit at the next floor bump.
- v2.1.183 floor: four newly-documented native sub-agent prompts to diff (provisional classifications, pending full diff at next floor bump — do NOT fetch the Piebald-AI files until then):
  - `agent-prompt-plan-mode-enhanced` (~715 tks) → compare to `teams/roles/planner.md` (provisional: likely overlap on plan structure)
  - `agent-prompt-claudemd-creation` → compare to root `CLAUDE.md` authoring guidance (provisional: consistent)
  - `agent-prompt-agent-creation-architect` (~1110 tks) → compare to `teams/orchestrator.md` sub-agent spawning (provisional: consistent)
  - `agent-prompt-claude-guide-agent` → compare to `teams/roles/base.md` guardrails (provisional: consistent)

## Related
- `CLAUDE/skills/required-minimum-version-pin.md` — the pinned CLI floor that anchors which tracker version to compare.
- `CLAUDE/skills/role-inheritance-pattern.md` — where shared role text lives (compare base.md once, not per role).

## Source
Piebald-AI/claude-code-system-prompts — https://github.com/Piebald-AI/claude-code-system-prompts (~11k stars)
