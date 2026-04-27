# Skills Folder

This folder contains **reusable skills** — short markdown files that capture patterns, conventions, and how-to knowledge discovered during team pipeline runs.

## Purpose

The team orchestrator automatically scans this folder and injects relevant skills into sub-agent prompts. This gives agents institutional knowledge without manual context sharing.

## Three-Tier Structure

Skill files use a progressive disclosure architecture to minimize token usage. Agents can decide whether to load full instructions based on the compact frontmatter alone.

### Tier 1: YAML Frontmatter (~100 tokens)
At the top of each file, a YAML block between `---` markers provides:
- `skill_name` — kebab-case identifier matching the filename
- `triggers` — list of when-to-use conditions (keywords/task types)
- `summary` — one-sentence description of what the skill covers

### Tier 2: Quick Reference (2-4 lines)
Immediately after the frontmatter heading, a `## Quick Reference` section provides key file paths, function signatures, or one-liner usage patterns. Agents can act on this for simple cases without reading the full instructions.

### Tier 3: Full Instructions
The existing `## When to Use`, `## Instructions`, `## Background`, and other sections remain unchanged. These provide complete detail for agents that need it.

## File Format

Each skill is a `.md` file with this structure:

```markdown
---
skill_name: my-skill-name
triggers:
  - When doing X
  - When debugging Y
summary: One-sentence description of this skill.
---

# Skill: <Name>

## Quick Reference
- Key file: `path/to/file.py`
- Main function: `do_thing()`
- Important constraint or gotcha

## When to Use
<description of when this skill is relevant — keywords, task types>

## Instructions
<reusable steps, patterns, conventions, or knowledge>
```

## Naming Convention

- Use **kebab-case** filenames: `add-websocket-message.md`, `android-new-screen.md`
- Keep names short but descriptive.

## Rules

- Each skill should be **under 50 lines** — a cheat-sheet, not a tutorial.
- Only capture **genuinely reusable** patterns, not one-off task details.
- The orchestrator creates at most **2 new skills per pipeline run**.
- `README.md` is excluded from skill collection.
