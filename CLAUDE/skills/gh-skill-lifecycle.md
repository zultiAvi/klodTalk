---
skill_name: gh-skill-lifecycle
triggers:
  - Installing or updating Claude Code skills via gh CLI
  - Publishing a custom skill to a GitHub repository
  - Managing installed skills or listing available skills
summary: Install, update, list, and publish Claude Code skills using the gh skill CLI commands.
---

# Skill: gh skill Lifecycle Management

## Quick Reference
- Install: `gh skill install <owner/repo>` or `gh skill install <owner/repo> --skill <name>`
- Update all: `gh skill update`
- List installed: `gh skill list`

## When to Use
When installing community skills from GitHub, updating existing skills, listing what is installed, or publishing a custom skill for others to use.

## Commands

### Install a Skill
```bash
gh skill install <owner/repo>                    # install all skills from repo
gh skill install <owner/repo> --skill <name>     # install a specific skill
```
Installs skill markdown files into the project's `CLAUDE/skills/` directory.

### Update Skills
```bash
gh skill update              # update all installed skills
gh skill update <owner/repo> # update skills from a specific repo
```

### List Installed Skills
```bash
gh skill list                # show all installed skills with source repos
```

### Publish a Skill
```bash
gh skill publish             # publish skills from current repo
```
Publishes skill files from `CLAUDE/skills/` so others can install them.

## KlodTalk Notes

- Skills are stored in `/workspace/CLAUDE/skills/` as markdown files.
- Security: set `disableSkillShellExecution: true` in frontmatter to prevent a skill from running shell commands.
- Follow three-tier progressive disclosure: YAML frontmatter, Quick Reference, full instructions.
- Keep skill files under 50 lines when possible.

## Source
Based on the official Anthropic skills protocol (github.com/anthropics/skills).
