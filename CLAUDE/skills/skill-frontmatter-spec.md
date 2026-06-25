---
skill_name: skill-frontmatter-spec
triggers:
  - Authoring a new KlodTalk skill and choosing which frontmatter fields to include
  - Aligning KlodTalk skill frontmatter with the upstream anthropics/skills canonical schema
  - Improving automatic skill recall during sub-agent prompt injection / tool-search
summary: "Upstream anthropics/skills (github.com/anthropics/skills) canonical SKILL.md schema adds an optional `description:` field — 2-3 keyword-rich prose sentences used by tool-search for semantic auto-selection, complementing KlodTalk's one-line `summary:`; add `description:` to NEW skills, keep `summary:` for compact display, do not retroactively update existing skills."
description: "Documents the optional description frontmatter field from the canonical anthropics/skills SKILL.md schema and how it complements KlodTalk's existing summary field. Use this when writing a new skill, deciding skill frontmatter fields, aligning with the upstream Anthropic skills specification, or improving semantic skill auto-selection and tool-search recall during sub-agent prompt injection."
---

# Skill: SKILL.md Frontmatter Spec (`description` Field)

## Quick Reference
- Upstream canonical schema: `anthropics/skills` — https://github.com/anthropics/skills (the official Anthropic agent-skills repository, ⭐155k).
- Adds an optional `description:` field — 2-3 keyword-rich prose sentences.
- Purpose: tool-search uses `description:` for **semantic** skill auto-selection; KlodTalk's one-line `summary:` stays for compact display.
- KlodTalk convention: **ADD `description:` to NEW skills**; keep `summary:`; existing skills need **no** retroactive update (the field is additive/optional).

## When to Use
When authoring a new skill in `CLAUDE/skills/`, or deciding whether to add frontmatter
fields beyond KlodTalk's traditional `skill_name:` / `triggers:` / `summary:`.

## The `description:` Field
The canonical `SKILL.md` schema treats `description:` as the primary semantic descriptor.
It should read as 2-3 prose sentences dense with the keywords and task phrasings an agent
would use when it needs this skill — this is what semantic tool-search matches against.
It complements (does not replace) KlodTalk's `summary:`, which remains a single compact
line for at-a-glance display in skill listings and prompt injection.

## KlodTalk Convention Going Forward
- NEW skills: include both `summary:` (one line) and `description:` (2-3 sentences).
- EXISTING skills: leave as-is; `description:` is optional and additive, so no mass migration.
- Keep `skill_name:` matching the kebab-case filename and `triggers:` as today.

## Compatibility / Future
Skills written to this schema stay compatible with the upstream spec, easing potential
contribution back to `anthropics/skills` or distribution via `/plugin install` once
KlodTalk's skill bundle is packaged.

## Cross-References
- `README.md` — the Skills Folder three-tier structure and frontmatter overview.
