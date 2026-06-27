---
skill_name: required-minimum-version-pin
triggers:
  - A version-gated hook or skill silently no-ops because the container CLI drifted
  - Hardening the agent container against Claude Code CLI version drift
  - Deciding the minimum Claude Code version KlodTalk's pipeline depends on
summary: "Claude Code (>= 2.1.163) refuses to start if the CLI is outside [requiredMinimumVersion, requiredMaximumVersion] managed settings; pin a floor (currently 2.1.195 for its three background-agent durability fixes — background jobs no longer disappear/lose data when written by a newer CLI, daemons no longer go unreachable on control-socket failure, and crash-reopen no longer shows a blank screen — plus the hyphenated hook-matcher exact-match change; the highest version any active KlodTalk hook/skill needs) to turn silent feature no-ops into a loud startup failure. Doc/config only — do NOT edit Dockerfile.agent."
---

# Skill: requiredMinimumVersion Managed-Settings Pin

## Quick Reference
- Keys: `requiredMinimumVersion` / `requiredMaximumVersion` (managed settings, Claude Code **>= 2.1.163**).
- Effect: the CLI **refuses to start** if its version is outside the configured range.
- Recommended floor: **2.1.195** (matches the highest version any active KlodTalk skill/hook depends on — the 2.1.195 background-agent durability fixes ensure background jobs are not lost/corrupted when written by a newer CLI, daemons stay reachable when the control socket fails, and crash-reopen does not show a blank screen for up to 5s (see `background-agent-durability.md`), and the hyphenated hook-matcher exact-match change makes `mcp__server-name` matchers exact-match — use `mcp__server-name__.*` to match all tools from a hyphenated MCP server (see `hyphenated-hook-matcher-exact-match.md`); the 2.1.193 `autoMode.classifyAllShell` setting routes ALL Bash/PowerShell through the auto-mode safety classifier for write-capable roles (see `classify-all-shell.md`), auto-mode denial reasons now surface in the transcript/toast/`/permissions` recent denials, idle background shell commands are reaped under memory pressure (disable via `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`), and the `claude_code.assistant_response` OTEL log event carries the model response text (see `otel-assistant-response-event.md`); the 2.1.191 ~37% streaming-CPU reduction cuts container throttling on heavy multi-turn runs, MCP capability-discovery retries reduce silent MCP connection failures in containers, the comma-separated hook-matcher fix makes `"Bash,Edit"` style matchers work as documented, sandbox network permission grants now persist across tool calls in a session, and `/rewind` restores context to before the last `/clear`; the 2.1.187 `sandbox.credentials` host-credential read block hardens KlodTalk's Docker agents against reading host secrets, see `sandbox-credentials-block.md`, the 5-minute MCP remote tool-call abort timeout prevents hung container agents on stalled MCP calls, and the structured-output infinite-re-call fix protects subagent schema flows; the 2.1.186 `respondToBashCommands` default flip is pinned `false` in KlodTalk's settings, see `respond-to-bash-commands.md`; the 2.1.185 stream-stall hint improvements make long-running container sessions more interpretable when the API stalls; the 2.1.183 auto-mode destructive-git/infra-destroy safety guards protect KlodTalk's autonomous nightly-scout commits, and `attribution.sessionUrl` lets the nightly bot suppress claude.ai session links in its commit/PR messages, see `attribution-session-url.md`; the 2.1.181 `/config key=value` inline syntax and `CLAUDE_CLIENT_PRESENCE_FILE` matter for per-stage session overrides; the 2.1.179 mid-stream connection-drop partial-response preservation matters for KlodTalk's long-running container sessions over WebSocket; the 2.1.178 MCP `disallowedTools` sub-agent enforcement fix matters for KlodTalk's reviewer/executor/validator role restrictions; the 2.1.176 hook `if`-condition matching fix and `enforceAvailableModels` allowlist enforcement matter for KlodTalk's model hardening; the 2.1.172 `CLAUDE_MEMORY_STORES` fix matters for KlodTalk's team memory recall in containerized/remote sessions; the `PostSession` lifecycle hook and `disableBundledSkills` need 2.1.169; the 2.1.170 transcript-save fix matters for KlodTalk's containerized launch path; `additionalContext` Stop hooks need 2.1.163; `waitingFor` needs 2.1.162).
- Location: workspace-level `/workspace/.claude/settings.json` (see `hook-settings-location.md`). DO NOT touch `Dockerfile.agent` (pinned per project realities).

## When to Use
- Many KlodTalk skills are version-gated and currently degrade by defensively
  handling a `null`/missing field on a drifted CLI. A managed-settings floor
  converts "feature silently unavailable" into a loud, early startup failure so
  drift is caught immediately instead of producing a quiet pipeline regression.

## Background
As of Claude Code 2.1.163, managed settings support `requiredMinimumVersion` and
`requiredMaximumVersion`. If the installed CLI falls outside that inclusive
range, Claude Code refuses to launch. Because `Dockerfile.agent` already pins the
CLI image, this pin is **complementary insurance**, not a replacement — keep the
floor in sync with the CLI version pinned in `Dockerfile.agent`.

Version-floor history (why the floor is where it is):
- **2.1.195 (2026-06-26): three background-agent durability fixes + hyphenated hook-matcher exact-match** — (1) background jobs no longer disappear from `claude agents` or lose data when written by a newer Claude Code version (a mixed host/container CLI-version hazard for KlodTalk's Docker agents); (2) background agent daemons no longer run unreachable when the control socket fails to start, which previously blocked restarts; (3) reopening a crashed background task no longer shows a blank screen for up to 5 seconds before restarting. These three protect KlodTalk's long-lived nightly-pipeline/Docker agent sessions whose state the `post_session_snapshot.sh` / `subagent_lifecycle_logger.sh` hooks depend on (see `background-agent-durability.md`). Also fixes hook matchers with hyphenated identifiers (e.g. `code-reviewer`, `mcp__brave-search`) accidentally substring-matching — they now exact-match; use `mcp__brave-search__.*` to match all tools from a hyphenated MCP server (KlodTalk has zero hyphenated matchers today, so this is forward-looking, see `hyphenated-hook-matcher-exact-match.md`). Also adds `CLAUDE_CODE_DISABLE_MOUSE_CLICKS` and voice-dictation/`/plugin` fixes (not KlodTalk-relevant). v2.1.194 was internal-only (no separate user-facing changelog entry). Current recommended floor.
- **2.1.193 (2026-06-26): `autoMode.classifyAllShell` setting + auto-mode denial-reason surfacing + idle background-shell memory-pressure reaping + `claude_code.assistant_response` OTEL log event** — `autoMode.classifyAllShell: true` routes ALL Bash/PowerShell commands through the auto-mode safety classifier instead of only arbitrary-code-execution patterns, a defense-in-depth lever for write-capable KlodTalk roles where a hard deny would break the role (see `classify-all-shell.md`; note KlodTalk launches `--dangerously-skip-permissions`, so treat this as forward-looking until verified active). Auto-mode denial reasons now surface in the transcript, the denial toast, and `/permissions` recent denials — useful for debugging KlodTalk's autonomous nightly-scout denials. Idle background shell commands are now reaped under memory pressure (disable via `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`). Adds the `claude_code.assistant_response` OpenTelemetry log event carrying the model's response text — a harness-native channel for capturing agent output alongside the existing JSONL hook pipeline (see `otel-assistant-response-event.md`).
- **2.1.191 (2026-06-24): comma-separated hook-matcher fix + MCP capability-discovery retries + sandbox network permission persistence + `/rewind` command + ~37% streaming CPU reduction** — comma-separated hook matchers (e.g. `"Bash,Edit"`) previously silently no-oped and matched nothing; 2.1.191 makes them work as documented, enabling future selective KlodTalk hooks (see `hook-comma-matcher-syntax.md`). MCP capability-discovery now retries instead of failing on the first miss, reducing silent MCP connection failures in KlodTalk's Docker agent containers. Sandbox network permission grants now persist across tool calls within a session instead of re-prompting each call. `/rewind` restores context to the state before the last `/clear` — a recovery option for long-running KlodTalk container sessions. The ~37% CPU reduction during streaming directly reduces container throttling on heavy multi-turn nightly runs.
- **2.1.187 (2026-06-23): `sandbox.credentials` host-credential read block + 5-minute MCP remote tool-call abort timeout + org-level model-restriction enforcement in the picker + structured-output infinite-re-call fix + `--resume` no-model-turns fix** — the 5-min MCP abort (override via `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`) prevents hung container agents when a remote MCP tool call stalls indefinitely. `sandbox.credentials` blocks sandboxed commands from reading host credential files and secret env vars, hardening KlodTalk's Docker agents that mount the host workspace against reading host secrets (see new `sandbox-credentials-block.md`). The structured-output fix stops the model re-calling `StructuredOutput` after a successful call and makes follow-up turns reliably return structured output, protecting KlodTalk subagent `agent({schema})` flows.
- **2.1.186 (2026-06-22): `respondToBashCommands` default flip + skill-frontmatter case-insensitivity + MCP `login`/`logout` + subagent schema-failure abort** — the default for `respondToBashCommands` flipped so a `!` bash command's output now auto-triggers a Claude response; KlodTalk pins it `false` to keep deterministic context-only behavior (see `respond-to-bash-commands.md`). Skill frontmatter keys now accept kebab/snake/camelCase and malformed `SKILL.md` YAML loads the body with empty metadata instead of failing silently. Adds `claude mcp login/logout` (non-interactive MCP auth) and a 5-attempt abort for `agent({schema})` subagents. NOTE: 2.1.186 also begins **enforcing** `Agent(type)`/`Agent(x,y)` named-subagent restrictions — but this remains a **no-op in KlodTalk** because `run_agent.py`/`run_claude_team.sh` launch with `--dangerously-skip-permissions`, which bypasses the permission engine regardless (see `tool-param-permission-syntax.md` + instinct #39).
- **2.1.185 (2026-06-20): stream-stall hint improvements** — the stall message wording changed to "Waiting for API response · will retry in …" and the silence threshold was raised from 10s to 20s before the hint appears; directly benefits KlodTalk's long-running Docker agent sessions where API stalls are common during heavy multi-turn runs, making a stalled stream interpretable instead of looking like a hang.
- **2.1.183 (2026-06-19): auto-mode destructive-git/infra-destroy safety guards + `attribution.sessionUrl` setting + thinking-block/WebSearch-in-subagents fixes** — adds confirmation guards that block destructive git operations (`reset --hard`, force-push) and infrastructure-destroy commands when running in autonomous/auto mode, which directly protects KlodTalk's nightly-scout agent that commits unattended. Introduces the `attribution.sessionUrl` setting (suppresses claude.ai session links in agent commit/PR messages, see `attribution-session-url.md`) — KlodTalk sets it `false` so bot commits stay link-free. Also fixes thinking-block rendering and `WebSearch` availability inside sub-agents.
- **2.1.181 (2026-06-18): `/config key=value` inline setting syntax + `CLAUDE_CLIENT_PRESENCE_FILE` + Bun 1.4** — subsumes the 2.1.179 connection-drop fix below. 2.1.181 adds `/config key=value` inline in-session setting syntax (ephemeral per-session override, see `inline-config-syntax.md`), the `CLAUDE_CLIENT_PRESENCE_FILE` env var (suppresses mobile push notifications while a client is attached), upgrades the bundled runtime to Bun 1.4, and improves line-by-line streaming of long paragraphs.
- **2.1.179 (2026-06-16): mid-stream connection-drop partial-response preservation + sandbox glob fix** — before this version, a WebSocket/network drop mid-response discarded the partially-received text; 2.1.179 preserves it, which matters for KlodTalk's long-running Docker agent sessions that stream for minutes at a time. Also fixes sandbox `denyRead`/`allowRead` glob matching on Linux (the KlodTalk container platform), so read-path restrictions are honored as written.
- **2.1.178 (2026-06-15): MCP `disallowedTools` sub-agent fix + `Tool(param:value)` permission syntax** — `disallowedTools` specs in sub-agent role files were silently ignored before this version; KlodTalk's `reviewer.md` / `executor.md` / `validator.md` / scout role restrictions rely on it being enforced. Also adds `Tool(param:value)` permission syntax (e.g. `Agent(model:claude-sonnet-4-6)`) for constraining sub-agent model at the permission-rule level (see `tool-param-permission-syntax.md`).
- **2.1.176 (2026-06-13): hook `if`-condition matching fix + `enforceAvailableModels`**
  — hook `if` conditions that match documented tool patterns (e.g. `Edit(src/**)`)
  were not evaluated correctly before this version; KlodTalk's `PostToolUse` /
  `PreToolUse` matchers rely on correct `if`-condition matching. 2.1.176 also lands
  `footerLinksRegexes` and Fable 5 auto-fallback, and subsumes the 2.1.174
  `enforceAvailableModels` / `availableModels` allowlist enforcement that KlodTalk's
  model-allowlist hardening depends on (see `enforce-available-models.md`).
- **2.1.172 (2026-06-10): CLAUDE_MEMORY_STORES fix** — team memory stores
  weren't found in remote/container sessions before this version; KlodTalk's
  team memory recall depends on it. (2.1.172 also raised the sub-agent nesting
  limit to 5 levels.)
- **2.1.170 (2026-06-09): transcript-save bug fix** — sessions launched from
  environments that set Claude Code env vars (KlodTalk's Docker containerized
  path) silently dropped session transcripts before this version. It also
  subsumes the 2.1.169 features below.
- **2.1.169**: `PostSession` lifecycle hook and `disableBundledSkills` setting
  (see `post-session-snapshot.md` and `disable-bundled-skills.md`).
- **2.1.163**: `additionalContext` Stop hooks; **2.1.162**: `waitingFor`.

## Settings Snippet
Add to `/workspace/.claude/settings.json`:

```json
{
  "requiredMinimumVersion": "2.1.195"
}
```

Optionally cap with a maximum to detect an unintended upgrade:

```json
{
  "requiredMinimumVersion": "2.1.195",
  "requiredMaximumVersion": "2.99.99"
}
```

## Keep In Sync
Whenever `Dockerfile.agent`'s pinned Claude Code version changes, update
`requiredMinimumVersion` to match (or to the highest version any active hook/skill
requires, whichever is higher). The two must not drift apart.

## Cross-References
- `hook-settings-location.md` — why this goes in the workspace-level settings file.
- `stop-hook-additional-context.md` — a 2.1.163-gated feature this floor protects.
- `enforce-available-models.md` — the 2.1.174+ `enforceAvailableModels` allowlist this floor guarantees is honored.
- `tool-param-permission-syntax.md` — the 2.1.178 `Tool(param:value)` permission syntax this floor unlocks.
- `disallowed-tools-frontmatter.md` — the role `disallowedTools:` restrictions the 2.1.178 sub-agent fix makes effective.
- `inline-config-syntax.md` — the 2.1.181 `/config key=value` inline setting syntax this floor unlocks.
- `attribution-session-url.md` — the 2.1.183 `attribution.sessionUrl` setting this floor unlocks.
- `respond-to-bash-commands.md` — the 2.1.186 `respondToBashCommands` default flip this floor pins to `false`.
- `classify-all-shell.md` — the 2.1.193 `autoMode.classifyAllShell` setting this floor unlocks.
- `otel-assistant-response-event.md` — the 2.1.193 `claude_code.assistant_response` OTEL log event this floor unlocks.
- `background-agent-durability.md` — the three 2.1.195 background-agent durability fixes this floor guarantees.
- `hyphenated-hook-matcher-exact-match.md` — the 2.1.195 hyphenated hook-matcher exact-match change this floor reflects.

## Source
- Claude Code CHANGELOG v2.1.163 / v2.1.169 / v2.1.170 / v2.1.172 / v2.1.174 / v2.1.176 / v2.1.178 / v2.1.179 / v2.1.181 / v2.1.183 / v2.1.185 / v2.1.186 / v2.1.187 / v2.1.191 / v2.1.193 / v2.1.195 —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
