---
skill_name: skill-creator
triggers:
  - Orchestrator Step 6 is about to write a new skill file to CLAUDE/skills/
  - Reviewing an existing skill for completeness before committing it
  - Deciding whether to create a new skill or amend an existing one for the same topic
summary: "Checklist for writing well-formed KlodTalk skills: required frontmatter fields (skill_name, triggers, summary), required body section order, an anti-patterns list, and an increment rule that says to amend an existing skill rather than duplicate it."
---

# Skill: Skill Creator

## Quick Reference
- Skill files live in the **first repo's** `CLAUDE/skills/` folder, filename kebab-case `.md` (e.g. `slack-btw-bridge.md`); the stem MUST equal the `skill_name` value.
- Frontmatter is YAML between `---` fences: `skill_name`, `triggers` (list), `summary` (double-quoted string).
- Body section order: `# Skill: <Name>` → `## Quick Reference` → `## When to Use` → `## Instructions` → `## Cross-References` (or `## Related`) → `## Source` (or `## Source Attribution`).
- Increment rule: if a skill already covers the topic, **amend it** — do not create a near-duplicate file.
- Authoritative field spec: github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md.

## When to Use
Apply this whenever the orchestrator's Step 6 reflection decides a reusable pattern is worth recording, or when auditing an existing skill that looks sparse (missing Quick Reference, vague triggers, or a summary that only makes sense after reading the body).

## Instructions

### Required Frontmatter Fields
- **`skill_name`** — kebab-case, MUST match the filename stem. Used as the stable identifier.
- **`triggers`** — a YAML list of 2–5 **concrete, observable events**, not topic labels. Each should describe a moment an agent can recognize ("a PostToolUse hook fires on a Bash command"), not a subject area ("hooks").
- **`summary`** — one or two sentences, self-contained, usable verbatim as a tool-call description. It must make sense without reading the body. Keep it a **double-quoted** string; a bare `key: value` substring inside an unquoted summary breaks the YAML parse (KlodTalk instinct).

### Required Body Section Order
1. **Quick Reference** — 1–6 bullet facts (file paths, version floor, the one-line contract).
2. **When to Use** — the concrete triggers restated in prose.
3. **Instructions** — the how-to. Include a **code/config snippet** whenever the skill touches a config file, hook payload, or settings.json shape.
4. **Cross-References / Related** — link sibling skills by filename.
5. **Source / Source Attribution** — origin repo + URL + stars, or "official" for Anthropic repos.

### Anti-Patterns Checklist (reject the skill if any apply)
- **Vague topic-name triggers** — bad: "when using hooks"; good: "when a PostToolUse hook fires on a Bash command".
- **Summary that needs the body** — if you must read the Instructions to understand the summary, rewrite the summary.
- **Missing config snippet** — a skill about configuration with no example payload/settings block is incomplete.
- **Duplicating an existing skill** — a new file whose topic overlaps an existing one without adding anything distinct.

### Increment Rule
Before creating a new file, scan the existing `CLAUDE/skills/` set (the Available Skills section). If a skill already covers the topic, **extend or amend that file** instead. Only create a new file when the topic is genuinely distinct from every existing skill. This keeps the skill set deduplicated and lets each nightly run build on the last.

## Cross-References
- `session-start-title.md` — example of a clean frontmatter + body following these conventions.
- `stop-hook-additional-context.md` — example of a config-snippet-bearing skill.
- Orchestrator Step 6 (`teams/orchestrator.md`) — where skill creation is triggered.

## Source Attribution
- `anthropics/skills` (official Anthropic repo): https://github.com/anthropics/skills — authoritative agent-skills spec (`spec/agent-skills-spec.md`); official, no star count applicable.
- `Piebald-AI/claude-code-system-prompts` (community): https://github.com/Piebald-AI/claude-code-system-prompts — exact loader frontmatter schema, updated each Claude Code release; stars not confirmed.
- `bobmatnyc/claude-mpm` (community): https://github.com/bobmatnyc/claude-mpm — bundled skill-creator pattern; stars not confirmed.
