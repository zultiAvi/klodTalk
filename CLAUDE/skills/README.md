# Skills Folder

This folder contains **reusable skills** — short markdown files that capture patterns, conventions, and how-to knowledge discovered during team pipeline runs.

## Purpose

The team orchestrator automatically scans this folder and injects relevant skills into sub-agent prompts. This gives agents institutional knowledge without manual context sharing.

## File Format

Each skill is a `.md` file with this structure:

```markdown
# Skill: <Name>

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
