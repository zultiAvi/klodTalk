---
skill_name: required-minimum-version-pin
triggers:
  - A version-gated hook or skill silently no-ops because the container CLI drifted
  - Hardening the agent container against Claude Code CLI version drift
  - Deciding the minimum Claude Code version KlodTalk's pipeline depends on
summary: "Claude Code (>= 2.1.163) refuses to start if the CLI is outside [requiredMinimumVersion, requiredMaximumVersion] managed settings; pin a floor (currently 2.1.185, the highest version any active KlodTalk hook/skill needs) to turn silent feature no-ops into a loud startup failure. Doc/config only — do NOT edit Dockerfile.agent."
---

# Skill: requiredMinimumVersion Managed-Settings Pin

## Quick Reference
- Keys: `requiredMinimumVersion` / `requiredMaximumVersion` (managed settings, Claude Code **>= 2.1.163**).
- Effect: the CLI **refuses to start** if its version is outside the configured range.
- Recommended floor: **2.1.185** (matches the highest version any active KlodTalk skill/hook depends on — the 2.1.185 stream-stall hint improvements make long-running container sessions more interpretable when the API stalls; the 2.1.183 auto-mode destructive-git/infra-destroy safety guards protect KlodTalk's autonomous nightly-scout commits, and `attribution.sessionUrl` lets the nightly bot suppress claude.ai session links in its commit/PR messages, see `attribution-session-url.md`; the 2.1.181 `/config key=value` inline syntax and `CLAUDE_CLIENT_PRESENCE_FILE` matter for per-stage session overrides; the 2.1.179 mid-stream connection-drop partial-response preservation matters for KlodTalk's long-running container sessions over WebSocket; the 2.1.178 MCP `disallowedTools` sub-agent enforcement fix matters for KlodTalk's reviewer/executor/validator role restrictions; the 2.1.176 hook `if`-condition matching fix and `enforceAvailableModels` allowlist enforcement matter for KlodTalk's model hardening; the 2.1.172 `CLAUDE_MEMORY_STORES` fix matters for KlodTalk's team memory recall in containerized/remote sessions; the `PostSession` lifecycle hook and `disableBundledSkills` need 2.1.169; the 2.1.170 transcript-save fix matters for KlodTalk's containerized launch path; `additionalContext` Stop hooks need 2.1.163; `waitingFor` needs 2.1.162).
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
- **2.1.185 (2026-06-20): stream-stall hint improvements** — the stall message wording changed to "Waiting for API response · will retry in …" and the silence threshold was raised from 10s to 20s before the hint appears; directly benefits KlodTalk's long-running Docker agent sessions where API stalls are common during heavy multi-turn runs, making a stalled stream interpretable instead of looking like a hang. Current recommended floor.
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
  "requiredMinimumVersion": "2.1.185"
}
```

Optionally cap with a maximum to detect an unintended upgrade:

```json
{
  "requiredMinimumVersion": "2.1.185",
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

## Source
- Claude Code CHANGELOG v2.1.163 / v2.1.169 / v2.1.170 / v2.1.172 / v2.1.174 / v2.1.176 / v2.1.178 / v2.1.179 / v2.1.181 / v2.1.183 / v2.1.185 —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
