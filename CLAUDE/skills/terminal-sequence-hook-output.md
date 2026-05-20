---
skill_name: terminal-sequence-hook-output
triggers:
  - Authoring a hook that needs to emit a desktop notification, terminal bell, or window-title change
  - Configuring KlodTalk Docker containers for workload identity federation
  - Reviewing hook JSON output schemas added in Claude Code v2.1.141+
summary: "Claude Code v2.1.141 adds two distinct items: (a) hooks may return a `terminalSequence` field in JSON output that the CLI writes to the terminal (bells, OSC title changes, notifications) without affecting agent behavior; (b) `ANTHROPIC_WORKSPACE_ID` env var must be forwarded into Docker containers when the deployment uses workload identity federation."
---

# Skill: `terminalSequence` Hook Output + `ANTHROPIC_WORKSPACE_ID` (v2.1.141)

## Quick Reference
- Hook JSON output field: `"terminalSequence"` (string -- ANSI/OSC escape sequence)
- Available since: Claude Code v2.1.141
- Effect: the CLI emits the sequence to the terminal device, not to the agent. Safe for observational hooks -- does not change exit-0 discipline.
- New env var: `ANTHROPIC_WORKSPACE_ID` -- required for workload identity federation deployments. Must be forwarded into KlodTalk agent containers.

## When to Use
- Adding a hook that should ring the terminal bell on a pipeline milestone (e.g., nightly run complete).
- Wiring a desktop-notification escape (OSC 9 / OSC 777) into a PostToolUse logger.
- Operating KlodTalk under workload identity federation (no static API key) and seeing identity-federation requests rejected.

## Instructions

### `terminalSequence` JSON Field
A hook script may print a JSON object to stdout containing `terminalSequence` alongside its normal payload. The CLI extracts the field and writes the escape string to the controlling terminal (or skips it silently when none is attached). Examples:
- Terminal bell: `"terminalSequence": "\u0007"`
- OSC window-title: `"terminalSequence": "\u001b]0;Nightly Scout complete\u0007"`
- OSC 9 desktop notification (iTerm2/Terminal.app): `"terminalSequence": "\u001b]9;Pipeline finished\u0007"`

Because the CLI -- not the agent -- consumes the field, hooks that emit it remain purely observational and should still follow the exit-0 discipline from `hook-event-logging.md`. Do NOT use `terminalSequence` to attempt to inject control instructions back to the agent; the agent never sees the string.

### Sample Hook Snippet
```bash
# Emit a terminal bell when a Write tool call completes inside the nightly team folder.
if [ -n "${FILE_PATH}" ] && echo "${FILE_PATH}" | grep -q "/.klodTalk/team/current/"; then
    echo '{"terminalSequence":"\u0007"}'
fi
exit 0
```

### `ANTHROPIC_WORKSPACE_ID` Env Var
Workload identity federation deployments rely on the workspace ID being present in every Claude Code invocation. When KlodTalk runs agents inside Docker (`docker exec`-based `run_agent.py`), the host environment is not inherited; the workspace ID is dropped and federation requests are rejected silently.

When operating under federation, ensure the container env block forwards the variable:
- For `docker run` based startups: add `-e ANTHROPIC_WORKSPACE_ID` (re-exports the host value).
- For `docker exec` based agent execution: pass `-e ANTHROPIC_WORKSPACE_ID="${ANTHROPIC_WORKSPACE_ID}"`.
- For OAuth-session deployments (the KlodTalk default), the variable is unused and can be omitted.

### Cross-Reference
- `hook-event-logging.md` -- the legacy exit-0 discipline that `terminalSequence`-emitting hooks must still follow.
- `session-data-path-propagation.md` -- the parallel container-env propagation pattern for `KLOD_SESSION_DATA_PATH`.
- `continue-on-block-hooks.md` -- when a hook must actually refuse a tool call; orthogonal to `terminalSequence`.

## Source
Claude Code v2.1.141 release notes -- https://github.com/anthropics/claude-code/releases/tag/v2.1.141 (github.com/anthropics/claude-code).
