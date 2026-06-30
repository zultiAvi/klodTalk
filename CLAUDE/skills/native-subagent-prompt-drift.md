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
- Tracks every native sub-agent prompt (Plan / Explore / Task) + all built-in tool descriptions, per CLI release (tracker current with v2.1.196 floor as of 2026-06-30).
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
- v2.1.195 floor (CONFIRMED 2026-06-29): the four provisional prompt types were fetched and diffed. Tracker tag used: **v2.1.195** (commit `7b9ccd1`) — the tracker is current with the KlodTalk floor (no lag this run). Files under `system-prompts/` on the tracker. Per-prompt classifications:
  - `agent-prompt-plan-mode-enhanced` (tracker header `ccVersion: 2.1.118`) ↔ `teams/roles/planner.md` → **conflicting (intentional override, left as-is)**. The native prompt is STRICT READ-ONLY ("STRICTLY PROHIBITED from creating/modifying/deleting files … you do NOT have access to file editing tools"). KlodTalk's planner is deliberately NOT read-only: it writes `plan.md`/`plan_meta.txt` and, for SIMPLE tasks, implements code directly (Write/Edit kept available — see planner.md frontmatter comment). This is a documented KlodTalk design choice, not accidental drift; the existing frontmatter comment already records why Write/Edit stay. No edit needed. Plan-structure framing (explore → design → step-by-step → critical files) overlaps and is consistent.
  - `agent-prompt-claudemd-creation` (tracker header `ccVersion: 2.1.185`) ↔ root `CLAUDE.md` authoring guidance → **consistent (no overlapping instructions; nothing to drift)**. KlodTalk's root `CLAUDE.md` is the artifact itself, not a prompt that tells an agent HOW to author a CLAUDE.md, so there is no competing instruction set. The native "do not include obvious/generic instructions; focus on big-picture architecture" guidance is in fact echoed by KlodTalk's actual CLAUDE.md style (architecture-first, no boilerplate). Left as-is.
  - `agent-prompt-agent-creation-architect` (tracker header `ccVersion: 2.0.77`) ↔ `teams/orchestrator.md` sub-agent spawning section → **consistent (non-overlapping scope)**. Native authors NEW agent specs as a JSON object (`identifier`/`whenToUse`/`systemPrompt`). KlodTalk's orchestrator spawns sub-agents from fixed role `.md` files via the Agent tool and never authors new agent JSON specs, so there is no contradictory instruction. Left as-is.
  - `agent-prompt-claude-guide-agent` (tracker header `ccVersion: 2.1.154`) ↔ `teams/roles/base.md` guardrails → **consistent (non-overlapping scope)**. Native is a docs-lookup helper (Claude Code / Agent SDK / Claude API guidance via WebFetch). base.md guardrails cover code quality, commit rules, and the workspace-auth refusal override — no shared subject matter, no conflict. Left as-is.
  - Net: zero edits to any role file required this run. The one "conflict" (planner read-only) is a pre-existing intentional override already documented in `planner.md`. Re-run this audit at the next floor bump.
- v2.1.196 floor (CONFIRMED 2026-06-30): re-ran the deferred audit at the new floor bump. Tracker tag used: **v2.1.196** (the tracker is current with the KlodTalk floor — no lag this run; v2.1.196 was the most recent tag, released 2026-06-29, "+1,869 tokens" vs v2.1.195). Fetched the same four prompt files under `system-prompts/` and diffed against the same KlodTalk counterparts. The four prompt files are UNCHANGED at v2.1.196 — every tracker header is identical to the v2.1.195 run, confirming v2.1.196 introduced no edits to these sub-agent prompts:
  - `agent-prompt-plan-mode-enhanced` (tracker header `ccVersion: 2.1.118`, unchanged) ↔ `teams/roles/planner.md` → **conflicting (intentional override, left as-is)** — same as v2.1.195: native prompt is STRICT READ-ONLY; KlodTalk's planner deliberately writes plan files and implements SIMPLE tasks directly (documented in planner.md frontmatter). No edit.
  - `agent-prompt-claudemd-creation` (tracker header `ccVersion: 2.1.185`, unchanged) ↔ root `CLAUDE.md` authoring guidance → **consistent** — no competing instruction set; KlodTalk's CLAUDE.md is architecture-first with no boilerplate, echoing the native "no obvious/generic instructions" guidance. No edit.
  - `agent-prompt-agent-creation-architect` (tracker header `ccVersion: 2.0.77`, unchanged) ↔ `teams/orchestrator.md` sub-agent spawning section → **consistent (non-overlapping scope)** — native authors NEW agent JSON specs; KlodTalk's orchestrator spawns from fixed role `.md` files and never authors agent JSON. No edit.
  - `agent-prompt-claude-guide-agent` (tracker header `ccVersion: 2.1.154`, unchanged) ↔ `teams/roles/base.md` guardrails → **consistent (non-overlapping scope)** — native is a docs-lookup helper; base.md covers code quality/commit rules/workspace-auth override. No shared subject matter. No edit.
  - Net: zero edits to any role file required this run (identical outcome to v2.1.195 — the four prompts did not change between floors). The one "conflict" (planner read-only) remains a pre-existing intentional override already documented in `planner.md`; `teams/roles/base.md` was NOT touched (instinct #29 — it carries pre-existing unstaged drift and no real conflict was found). Re-run this audit at the next floor bump.

## Related
- `CLAUDE/skills/required-minimum-version-pin.md` — the pinned CLI floor that anchors which tracker version to compare.
- `CLAUDE/skills/role-inheritance-pattern.md` — where shared role text lives (compare base.md once, not per role).

## Source
Piebald-AI/claude-code-system-prompts — https://github.com/Piebald-AI/claude-code-system-prompts (~11k stars)
