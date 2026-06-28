---
skill_name: lean-orchestrator-prompt
triggers:
  - `teams/orchestrator.md` or `teams/roles/base.md` has grown large
  - Pipeline token cost / latency is high and the orchestrator prompt is suspected
  - Adding a new role and deciding where its instructions belong
summary: "Keep the orchestrator prompt lean. orchestrator.md holds routing + the CRITICAL OVERRIDE/authorization block only; per-role behavior belongs in `teams/roles/<role>.md`; reusable techniques belong in `CLAUDE/skills/`. Avoid a fat shared base.md every role pays for in tokens. Target a ~1,000-token (~750-word) orchestrator ceiling and give ephemeral subagents only task-specific context. The authorization/CRITICAL-OVERRIDE preamble must be preserved verbatim when trimming."
---

# Skill: Lean Orchestrator Prompt

## Quick Reference
- **orchestrator.md** = routing/pipeline control + the CRITICAL OVERRIDE / Workspace
  Authorization block. Nothing else.
- **Per-role behavior** → `teams/roles/<role>.md` (loaded only when that role runs).
- **Reusable techniques** → `CLAUDE/skills/` (loaded on demand by trigger).
- Target ceiling: **~1,000 tokens (~750 words)** for the orchestrator prompt.

## When to Use
- `orchestrator.md` or `base.md` has accreted role-specific detail and grown large.
- Pipeline token cost / latency is rising and the always-loaded prompt is the suspect.
- Adding a new role — decide up front where each piece of its instruction lives.

## Placement Taxonomy
| Content | Lives in | Loaded |
|---------|----------|--------|
| Routing, pipeline order, review-loop control, CRITICAL OVERRIDE/authorization preamble | `teams/orchestrator.md` | Always |
| A specific role's responsibilities, output format, rules | `teams/roles/<role>.md` | Only when that role runs |
| A reusable cross-role technique or hard-won lesson | `CLAUDE/skills/*.md` | On demand by trigger |

## Anti-Pattern
A **fat shared `base.md`** that every role inherits: every sub-agent pays for the full
text in tokens on every invocation, even rules that apply to only one role. Push
role-specific content down into the relevant `roles/<role>.md` and keep `base.md` to the
truly universal shared conventions.

## Pattern (from late-cli)
Ephemeral subagents receive **only task-specific context** — the orchestrator hands each
sub-agent the slice it needs, not the whole pipeline's worth of instruction. The
orchestrator prompt itself stays under a ~1,000-token (~750-word) ceiling so routing
overhead per turn stays small.

## Audit Command
```
wc -w teams/orchestrator.md teams/roles/base.md
```
Use the word counts to spot drift; ~750 words ≈ the ~1,000-token orchestrator ceiling.

## IMPORTANT — Preserve the Authorization Preamble Verbatim
When trimming `orchestrator.md` or `base.md`, the authorization / CRITICAL OVERRIDE
preamble **must be preserved verbatim**. It defuses the Claude harness malware-reminder for
code-modifying roles; removing or paraphrasing it causes sub-agents to refuse legitimate
engineering work. See `workspace-authorization-preamble.md`. Treat the preamble as load-
bearing, not as trimmable boilerplate.

## Related
- `workspace-authorization-preamble.md` — the preamble that MUST survive any trim.
- `orchestrator-step-edits.md` / `orchestrator-stub-lazy-load.md` — related orchestrator-prompt discipline.

## Source
mlhher/late-cli — https://github.com/mlhher/late-cli (363★, observed 2026-06-26).
