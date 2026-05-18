---
skill_name: stop-hook-block-cap
triggers:
  - Writing or auditing a Stop hook that may repeatedly block the same action
  - Diagnosing a session that terminates silently mid-pipeline
  - Configuring KlodTalk nightly agent worktree behavior
summary: "Claude Code v2.1.143 caps Stop hooks at 8 consecutive blocks before terminating the session, and `worktree.bgIsolation: \"none\"` disables worktree isolation for background sessions in KlodTalk-managed containers."
---

# Skill: Stop-Hook 8-Block Cap and `worktree.bgIsolation` (v2.1.143)

## Quick Reference
- Stop hooks that return non-zero are capped at **8 consecutive blocks** in Claude Code v2.1.143+. After the 8th block the session terminates rather than looping forever.
- Mitigation: a Stop hook should `exit 0` (pass-through) once its retry budget is spent, or use `continueOnBlock: true` (PostToolUse only) so the rejection reason is surfaced.
- `worktree.bgIsolation: "none"` in `.claude/settings.json` disables automatic worktree creation for background sessions — appropriate for KlodTalk where `run_claude_team.sh` already manages worktrees.

## When to Use
- Authoring or auditing any `Stop` hook entry in `.claude/settings.json`.
- Investigating a nightly run that ended without a final summary or commit.
- Configuring a KlodTalk container that has its own worktree management.

## Instructions

### The 8-Block Cap
A Stop hook that exits non-zero blocks the session-stop event and asks Claude to continue. Before v2.1.143 this could loop indefinitely. From v2.1.143 onward, after 8 consecutive blocks Claude Code terminates the session with no final summary. To avoid silent termination:
- Track retry count in the hook (e.g., write a counter file under `/tmp/`) and `exit 0` once the budget is exhausted.
- For pure enforcement use cases, prefer a `PostToolUse` hook with `continueOnBlock: true` (see `continue-on-block-hooks.md`) — the rejection reason is fed back to Claude instead of consuming a block slot.

### Disabling Background Worktree Isolation
KlodTalk's nightly agent runs as a background session inside a container that already has `/workspace` mounted. The default isolated-worktree mode copies edits into a sandbox that does not survive container exit, making changes appear lost. Add to the container's `.claude/settings.json`:
```json
{ "worktree": { "bgIsolation": "none" } }
```

## Related
- `continue-on-block-hooks.md` — modern PostToolUse alternative when a hook genuinely needs to refuse a call.
- `background-session-isolation.md` — full v2.1.143 worktree.bgIsolation discussion.
- `hook-event-logging.md` — legacy "always exit 0" discipline for observational hooks.

## Source
Claude Code CLI v2.1.143 release notes — https://github.com/anthropics/claude-code/releases (github.com/anthropics/claude-code).
