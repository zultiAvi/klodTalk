---
skill_name: sandbox-credentials-block
triggers:
  - Hardening a KlodTalk Docker agent against reading host credential files or secret env vars
  - A sandboxed agent command unexpectedly reads ~/.aws, ~/.ssh, or a host .env
  - Deciding whether to enable sandbox.credentials after bumping the CLI floor to 2.1.187
summary: "sandbox.credentials managed setting (CLI >= 2.1.187) blocks sandboxed Claude commands from reading host credential files (~/.aws, ~/.ssh, .env) and secret env vars — defense-in-depth for KlodTalk agents that mount the host workspace. Doc-only: verify exact JSON shape in the raw CHANGELOG before applying to settings.json."
---

# Skill: sandbox.credentials Host-Credential Read Block

## Quick Reference
- Key: `sandbox.credentials` (managed settings, Claude Code **>= 2.1.187**).
- Effect: blocks sandboxed commands from reading host credential files (e.g. `~/.aws`, `~/.ssh`, `.env`) and secret environment variables.
- Location: workspace-level `/workspace/.claude/settings.json` (see `hook-settings-location.md`).
- Status: **DOC-ONLY** — the exact JSON key shape is NOT yet confirmed from the raw changelog; do NOT add it to settings.json until verified.

## When to Use
KlodTalk mounts the host workspace into each Docker agent container, and agents run with `--dangerously-skip-permissions`. `sandbox.credentials` is defense-in-depth: even an agent that wanders outside its workspace cannot read host secrets like cloud-provider credentials, SSH keys, or `.env` files. Enable it once you have confirmed the precise JSON shape against the raw CHANGELOG.

## Instructions
The v2.1.187 changelog entry reads: "Added `sandbox.credentials` setting to block sandboxed commands from reading credential files and secret environment variables." It does **not** publish the exact JSON hierarchy. The most-likely shape is a nested object:

```json
{
  "sandbox": {
    "credentials": false
  }
}
```

**Verify exact JSON shape in raw CHANGELOG before applying** — it may instead be a flat `"sandbox.credentials"` key or take a value other than a boolean. WebFetch `https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`, locate the v2.1.187 entry, and confirm the precise key/value before writing it to `/workspace/.claude/settings.json`. Do NOT fabricate the config (hard project rule).

## Cross-References
- `required-minimum-version-pin.md` — the 2.1.187 floor that gates this setting.
- `container-network-allowlist.md` — companion container isolation hardening (per-project egress allowlist).
- `hook-settings-location.md` — why this goes in the workspace-level settings file.

## Source
- Claude Code CHANGELOG v2.1.187 (2026-06-23) — https://github.com/anthropics/claude-code/releases (github.com/anthropics).
