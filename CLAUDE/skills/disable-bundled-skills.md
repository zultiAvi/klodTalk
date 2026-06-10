---
skill_name: disable-bundled-skills
triggers:
  - Role agents reaching for generic bundled built-ins instead of KlodTalk skills
  - Reducing skill-surface noise / context clutter for reviewer, disprover, scout roles
  - Wanting CLAUDE/skills/ to be the sole intended skill surface
summary: "disableBundledSkills (Claude Code >= 2.1.169) removes the bundled Anthropic skills from the model's visible surface entirely, so agents see only KlodTalk's CLAUDE/skills/; complementary to skillOverrides."
---

# Skill: disableBundledSkills

## Quick Reference
- Key: `"disableBundledSkills": true` in `/workspace/.claude/settings.json`,
  alongside the companion skill-surface control `"disableSkillShellExecution": true`.
- Requires Claude Code **>= 2.1.169**. Older CLIs ignore the unknown key.
- Effect: removes bundled Anthropic skills from the model's visible surface
  entirely (different from `skillOverrides`, which only changes invocation mode
  for skills that remain visible).

## Rationale
KlodTalk ships ~80 custom skills in `CLAUDE/skills/` — these are the sole
intended skill surface. Bundled Anthropic skills surface in the same namespace,
adding context noise and occasionally shadowing a KlodTalk-specific alternative.
Disabling them sharpens agent focus and makes behavior more deterministic —
especially for reviewer, disprover, and scout roles that should only ever see
KlodTalk-purpose skills.

## Interaction with `skill-overrides-per-role.md`
Complementary layers, applied in order:
1. `disableBundledSkills` — removes the built-in skills from the surface.
2. `skillOverrides` (per-role) — controls the invocation mode (`off` /
   `user-invocable-only` / `name-only`) of the *remaining* (KlodTalk) skills.
Together they give full control over what each role can see and invoke.

## Before Enabling — Pre-flight Grep
Confirm no role prompt depends on a bundled built-in *slash command* by name:

```bash
grep -rn "/build\b\|/doctor\b\|/memory\b\|/mcp\b\|/config\b\|/review\b\|/bug\b\|/pr_comments\b\|/vim\b\|/terminal\b" \
  /workspace/teams/roles/ /workspace/teams/teams/ 2>/dev/null
```

Expected: empty (KlodTalk roles reference `CLAUDE/skills/` paths, not built-in
slash commands). If a real hit appears, create a matching `CLAUDE/skills/` entry
before enabling. (Confirmed empty as of 2026-06-10 — the only match was a
`@github/mcp-server` MCP allowlist entry, not a bundled slash command.)

## Validate
`python3 -m json.tool /workspace/.claude/settings.json` after editing.

## Cross-References
- `skill-overrides-per-role.md` — per-role invocation-mode control (layer 2).
- `required-minimum-version-pin.md` — the 2.1.169/2.1.170 version floor.

## Source
- anthropics/claude-code CHANGELOG v2.1.169 —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
