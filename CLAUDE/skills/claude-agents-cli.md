---
skill_name: claude-agents-cli
triggers:
  - Inspecting running/blocked/done Claude Code sessions on the host
  - Spawning a session with a specific model, effort, settings, or MCP config
  - Correlating subagent API logs back to a parent session
  - Wanting Claude to continue autonomously until a stated completion condition
summary: Use `claude agents` (v2.1.139+) with `--cwd /workspace` and the new flags (`--model`, `--effort`, `--settings`, `--mcp-config`, `--permission-mode`, `--dangerously-skip-permissions`, v2.1.142) to inspect and launch sessions; use `/goal` for autonomous-continuation prompts; correlate subagent logs via `x-claude-code-agent-id` headers.
---

# Skill: `claude agents` CLI, `/goal` Command, and Subagent Correlation

## Quick Reference
- List sessions: `claude agents --cwd /workspace`
- Spawn flags (v2.1.142): `--model`, `--effort`, `--settings`, `--mcp-config`, `--permission-mode`, `--dangerously-skip-permissions`
- Autonomous continuation: `/goal <completion condition>` -- Claude continues until the condition is met
- Subagent log headers: `x-claude-code-agent-id`, `x-claude-code-parent-agent-id`
- MCP env (v2.1.139+): `CLAUDE_PROJECT_DIR` is now injected into MCP stdio servers

## When to Use
- An operator needs to see which KlodTalk agent sessions are currently running, blocked, or done -- scoped to `/workspace`.
- Spawning an ad-hoc session that should match a team role's model/effort tier (Opus, Sonnet, Haiku; effort levels).
- Debugging a multi-step pipeline where a subagent's API request needs to be traced back to its parent session.
- Drafting a prompt that should run to a clearly stated termination condition rather than a single response.

## Instructions

### Listing Sessions
```bash
claude agents --cwd /workspace
```
Shows running, blocked, and done sessions whose working directory is under `/workspace`. The `--cwd` flag (v2.1.141+) scopes the list so other projects on the same host don't clutter the view. Without `--cwd`, all sessions for the user are listed.

### Spawning with New Flags (v2.1.142)
The following flags can be passed to `claude` (and `claude agents` where applicable) to control session behavior:

| Flag | Purpose |
|------|---------|
| `--model <name>` | Pick a model tier (matches the `model:` column in KlodTalk team `.md` files) |
| `--effort <level>` | Pick an effort level (low/medium/high) -- propagates as `$CLAUDE_EFFORT` to hooks |
| `--settings <path>` | Point at a specific `.claude/settings.json` file instead of the default |
| `--mcp-config <path>` | Use a specific MCP server configuration |
| `--permission-mode <mode>` | Override permission prompts (e.g., `acceptEdits`) |
| `--dangerously-skip-permissions` | Skip all permission prompts -- use with care |

These align directly with KlodTalk's per-role model selection in `run_claude_team.sh`. Prefer setting `--model` and `--effort` explicitly when launching ad-hoc sessions so the role's intended tier is preserved.

### `/goal` Command
Inside a Claude Code session:
```
/goal <completion condition expressed in natural language>
```
Claude continues iterating tool calls and reasoning until it judges the completion condition met (or it cannot make further progress). Useful when the task is iterative and a single prompt-response is insufficient, e.g., "run the tests and fix failures until all green."

Contrast with KlodTalk's "Start Working" mode: KlodTalk's file-based pipeline drives autonomous continuation externally via the orchestrator and role outputs; `/goal` is an in-session equivalent that lives entirely inside one Claude invocation. Do not combine the two for the same task -- pick one continuation mechanism.

### Subagent ID Headers (for Log Correlation)
Each subagent API request now carries:
- `x-claude-code-agent-id` -- the subagent's own ID
- `x-claude-code-parent-agent-id` -- the parent session's ID

When debugging a pipeline, capture these headers (from proxy logs, the Anthropic console, or a custom logging proxy) and join them back to the parent's `CLAUDE_CODE_SESSION_ID` value (see `session-id-in-bash-tools`). This is the only reliable way to correlate a deeply nested subagent's API activity with the originating KlodTalk team session.

### `CLAUDE_PROJECT_DIR` in MCP Servers (v2.1.139+)
MCP stdio servers spawned by Claude Code now receive `CLAUDE_PROJECT_DIR` in their environment, set to the project working directory. MCP servers should read it instead of hard-coding `/workspace` or accepting a path via custom config (see `mcp-frontmatter` for MCP config injection patterns).

## Related
- `session-id-in-bash-tools` -- `CLAUDE_CODE_SESSION_ID` env var in Bash subprocesses; the parent ID that the subagent headers reference.
- `mcp-frontmatter` -- MCP server configuration via role frontmatter; complements the `CLAUDE_PROJECT_DIR` injection.
- `hook-event-logging` -- `$CLAUDE_EFFORT` in hook env, set when `--effort` is passed.

## Source
- Claude Code v2.1.139 release notes (claude agents, /goal, subagent headers, CLAUDE_PROJECT_DIR in MCP): https://github.com/anthropics/claude-code/releases/tag/v2.1.139
- Claude Code v2.1.142 release notes (--model, --effort, --settings, --mcp-config, --permission-mode flags): https://github.com/anthropics/claude-code/releases/tag/v2.1.142
- Claude Code v2.1.141 release notes (--cwd scoping for `claude agents`): https://github.com/anthropics/claude-code/releases/tag/v2.1.141
