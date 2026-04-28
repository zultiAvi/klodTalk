---
skill_name: disable-skill-shell-exec
triggers:
  - Reviewing or updating `.claude/settings.json`
  - Hardening agent security
  - Diagnosing why skill inline shell blocks are not executing
summary: Block inline shell in skills via `disableSkillShellExecution`; force settings refresh via `forceRemoteSettingsRefresh`.
---

# Skill: disableSkillShellExecution and forceRemoteSettingsRefresh

## Quick Reference
- Settings in `.claude/settings.json`: `disableSkillShellExecution: true`, `forceRemoteSettingsRefresh: true`
- Prevents skill files from being used as shell escape vectors
- Override for dev: set `false` in `.claude/settings.local.json` (not committed)

## When to Use
When reviewing or updating `/workspace/.claude/settings.json`, hardening agent security, or diagnosing why skill inline shell blocks are not executing.

## Background

Claude Code CLI v2.1.107+ introduced two relevant policy settings:

1. **`disableSkillShellExecution`** -- Blocks inline shell execution (`!bash ...`) inside skills (`.md` files in `CLAUDE/skills/`) and slash commands. Prevents skill files from being used as a shell escape vector.

2. **`forceRemoteSettingsRefresh`** -- Forces agents to re-fetch remote policy settings on every startup. Critical for KlodTalk's long-lived Docker container sessions, which otherwise cache settings from container build time.

## Current State

Both settings are enabled in `/workspace/.claude/settings.json`:

```json
{
  "disableSkillShellExecution": true,
  "forceRemoteSettingsRefresh": true,
  ...
}
```

## Why This Matters for KlodTalk

KlodTalk agents run with access to the host Docker daemon (docker-in-docker). A skill file containing `!bash docker run ...` could bypass the role-level `disallowedTools` restrictions set in role frontmatter. `disableSkillShellExecution` closes this gap.

`forceRemoteSettingsRefresh` ensures that containers started from an older image still receive current policy settings on each `docker exec` call, rather than using cached settings from when the image was built.

## Overriding for Development

To temporarily allow skill shell execution in a development environment, set the flag to `false` in a project-local settings override:

```json
// .claude/settings.local.json (not committed)
{
  "disableSkillShellExecution": false
}
```

Do NOT disable this in the committed `/workspace/.claude/settings.json`.

## Relationship to disallowedTools

These two mechanisms are complementary, not overlapping:
- `disallowedTools` in role frontmatter: controls which Claude Code built-in tools a role agent can invoke.
- `disableSkillShellExecution`: controls whether skill/slash-command files can contain inline shell blocks.

Both should be set for a hardened agent.
