---
skill_name: orchestrator-stub-lazy-load
triggers:
  - SessionStart token cost is dominated by a large always-injected orchestrator prompt
  - Wanting to trim KlodTalk's per-session context overhead without losing orchestration logic
  - A hook needs to behave differently for the top-level session vs a spawned subagent
summary: "Forward-adoption reference: barkain/claude-code-workflow-orchestration injects a ~200-token orchestrator STUB on SessionStart and lazy-loads the full orchestration logic only on first delegation (~6.6K-token startup saving). Also documents the CLAUDE_PARENT_SESSION_ID env trick to detect subagent context inside hooks. Pattern source only — KlodTalk's orchestrator.md is currently injected in full."
---

# Skill: Stub-then-Lazy-Load Orchestrator Prompt

## Source
- Pattern from **barkain/claude-code-workflow-orchestration** (~71★, pushed 2026-06-20),
  https://github.com/barkain/claude-code-workflow-orchestration — surfaced by the
  2026-06-23 Nightly Scout GitHub pass. Pure Python 3.12 + `uv`, no MCP/npm deps.
- This skill documents the **transplantable patterns**, not the plugin itself. KlodTalk
  does not depend on the plugin.

## The Problem It Solves
KlodTalk injects `teams/orchestrator.md` (large — full pipeline spec, step list,
reporting contract) into context at SessionStart for every run, even runs that
never need the deep orchestration detail until the first delegation. That is a
fixed per-session token tax.

## Pattern 1 — Stub-then-lazy-load
- On SessionStart, inject only a **tiny stub** (~200 tokens / ~1.1KB): "you are an
  orchestrator; when you first need to delegate, read `commands/delegate.md`."
- The **full** orchestration logic lives in a separate file (`commands/delegate.md`
  in the source) and is loaded **only on first delegation**.
- Reported saving in the source: **~6.6K tokens** of SessionStart overhead per run.

### How KlodTalk could adopt it
- Split `teams/orchestrator.md` into a short SessionStart stub + a lazily-read
  `teams/orchestrator_full.md` (or per-phase files), referenced by path from the stub.
- Trade-off: adds one Read round-trip on first delegation and a second source of
  truth to keep in sync. Worth it only if SessionStart token cost is actually a
  measured bottleneck — measure `token_usage.json` SessionStart cost before/after.
- Caveat: KlodTalk's orchestrator currently relies on the full prompt being present
  up front for single-shot reasoning; verify the stub still carries the
  Workspace-Authorization preamble and Project-Instincts injection contract
  (see `workspace-authorization-preamble.md`) — those must NOT be lazy-loaded.

## Pattern 2 — `CLAUDE_PARENT_SESSION_ID` subagent detection in hooks
- Claude Code sets `CLAUDE_PARENT_SESSION_ID` in the environment of **spawned
  subagents** (absent in the top-level session). A `PreToolUse`/`PostToolUse` hook
  can branch on its presence to apply a rule to the top-level session only and
  **exempt subagents** (the source uses this so its "delegate?" nudge never fires
  inside a subagent that is itself doing the work).
- KlodTalk already filters subagent vs main via `hook-agent-type-filter.md` /
  `subagent-lifecycle-hooks.md`; `CLAUDE_PARENT_SESSION_ID` is a lighter-weight
  signal for the common "is this a subagent?" check when the agent *type* doesn't matter.

## Pattern 3 (noted, not recommended now) — graduated soft-enforcement
- The source escalates a delegation nudge per turn (silent → "delegate?" → hint →
  warning → strong reminder) instead of a hard hook block, resetting each user turn.
- KlodTalk currently prefers **hard** hook denies for safety-critical rules
  (`pre-tool-use-guard.md`, `auto-mode-hard-deny.md`). Soft-enforcement is a
  reasonable pattern for *advisory* nudges (e.g. "consider delegating") but should
  not replace the destructive-command hard blocks.

## When NOT to use
- Don't lazy-load anything security-relevant (auth preamble, deny-lists, instincts).
- Don't adopt Pattern 1 speculatively — only if SessionStart token cost is measured
  to be a real problem.
