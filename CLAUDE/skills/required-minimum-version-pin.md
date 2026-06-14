---
skill_name: required-minimum-version-pin
triggers:
  - A version-gated hook or skill silently no-ops because the container CLI drifted
  - Hardening the agent container against Claude Code CLI version drift
  - Deciding the minimum Claude Code version KlodTalk's pipeline depends on
summary: "Claude Code (>= 2.1.163) refuses to start if the CLI is outside [requiredMinimumVersion, requiredMaximumVersion] managed settings; pin a floor (currently 2.1.176, the highest version any active KlodTalk hook/skill needs) to turn silent feature no-ops into a loud startup failure. Doc/config only — do NOT edit Dockerfile.agent."
---

# Skill: requiredMinimumVersion Managed-Settings Pin

## Quick Reference
- Keys: `requiredMinimumVersion` / `requiredMaximumVersion` (managed settings, Claude Code **>= 2.1.163**).
- Effect: the CLI **refuses to start** if its version is outside the configured range.
- Recommended floor: **2.1.176** (matches the highest version any active KlodTalk skill/hook depends on — the 2.1.176 hook `if`-condition matching fix and `enforceAvailableModels` allowlist enforcement matter for KlodTalk's model hardening; the 2.1.172 `CLAUDE_MEMORY_STORES` fix matters for KlodTalk's team memory recall in containerized/remote sessions; the `PostSession` lifecycle hook and `disableBundledSkills` need 2.1.169; the 2.1.170 transcript-save fix matters for KlodTalk's containerized launch path; `additionalContext` Stop hooks need 2.1.163; `waitingFor` needs 2.1.162).
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
- **2.1.176 (2026-06-13): hook `if`-condition matching fix + `enforceAvailableModels`**
  — hook `if` conditions that match documented tool patterns (e.g. `Edit(src/**)`)
  were not evaluated correctly before this version; KlodTalk's `PostToolUse` /
  `PreToolUse` matchers rely on correct `if`-condition matching. 2.1.176 also lands
  `footerLinksRegexes` and Fable 5 auto-fallback, and subsumes the 2.1.174
  `enforceAvailableModels` / `availableModels` allowlist enforcement that KlodTalk's
  model-allowlist hardening depends on (see `enforce-available-models.md`). Current
  recommended floor.
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
  "requiredMinimumVersion": "2.1.176"
}
```

Optionally cap with a maximum to detect an unintended upgrade:

```json
{
  "requiredMinimumVersion": "2.1.176",
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

## Source
- Claude Code CHANGELOG v2.1.163 / v2.1.169 / v2.1.170 / v2.1.172 / v2.1.174 / v2.1.176 —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
