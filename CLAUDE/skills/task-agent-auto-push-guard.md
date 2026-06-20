---
skill_name: task-agent-auto-push-guard
triggers:
  - A Web/Android task-agent sub-agent attempts git push despite CLAUDE.md saying not to
  - Hardening KlodTalk guards so agents never push to the remote
  - Auditing why a claude/<task-id> branch appeared on the remote
summary: "The Web/Android task-agent sub-agent system prompt hard-codes a git push to claude/<task-id> (issue #56865), overriding CLAUDE.md's no-push rule; both KlodTalk guards now block ALL plain git push (not just --force) and the PreToolUse hook is the only defence since Anthropic has no fix ETA."
---

# Skill: Task-Agent Auto-Push Guard (issue #56865)

## Quick Reference
- Platform bug: the Web/Android task-agent sub-agent's built-in system prompt hard-codes `git push` to a `claude/<task-id>` branch, overriding any CLAUDE.md "do NOT push" instruction.
- KlodTalk agents must NEVER push — the server pushes after the agent finishes (see `git_instructions` in `server/run_agent.py`).
- Both guards previously blocked ONLY `git push --force`/`-f`, leaving a plain `git push` unguarded.
- Fix: block ALL plain `git push` in both guards.

## When to Use
- Reviewing or extending the destructive-command guards.
- Investigating an unexpected `claude/<task-id>` branch on the remote.
- Anytime the task-agent / sub-agent prompt behaviour is suspected of pushing.

## Instructions
The gap existed because instruction-level "do not push" (CLAUDE.md / base.md) cannot override a hard-coded push in the harness's own sub-agent prompt. Tool-call-level blocking is required:
- `server/utils/hooks/pre_tool_use_guard.sh`: deny pattern `git[[:space:]]+push([[:space:]]|$)` blocks any plain push; the `--force`/`-f` patterns remain (subsumed, kept for explicit intent).
- `server/run_agent.py`: inline `case` adds `*"git push"*) BLOCKED="git push is blocked (issue #56865 ...)"` AFTER the `--force`/`-f` cases so their specific messages still win.
- Caveat: Anthropic has acknowledged no ETA for a prompt-level fix, so the hook is the ONLY reliable defence — do not remove it expecting an upstream patch.

## Cross-References
- `pre-tool-use-guard.md` — the hook this rule lives in (deny-list + registration).
- `native-subagent-prompt-drift.md` — tracks the native sub-agent prompts whose hard-coded behaviour caused this gap.

## Source
anthropics/claude-code Issue #56865 — https://github.com/anthropics/claude-code/issues/56865
