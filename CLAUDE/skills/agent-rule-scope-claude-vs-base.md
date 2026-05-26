---
skill_name: agent-rule-scope-claude-vs-base
triggers:
  - User asks to add a coding rule, convention, or quality standard "for the agents"
  - Deciding whether a new rule belongs in CLAUDE.md or teams/roles/base.md
  - Reviewing where to place a project-wide vs cross-project policy
summary: "Rules in /workspace/CLAUDE.md apply to agents working on KlodTalk only. Rules in teams/roles/base.md apply to every team agent on every project. Place rules according to the intended scope; cross-posting is acceptable when both scopes need them."
---

# Skill: Where Agent Rules Live — CLAUDE.md vs base.md

## Quick Reference
- `/workspace/CLAUDE.md` -- repo-level instructions. Loaded only when an agent runs against the KlodTalk repo itself. Use for KlodTalk-specific conventions (file paths, message protocol, architecture).
- `teams/roles/base.md` -- inherited by every role via `<!-- inherits: base.md -->`. Loaded for every team agent on every project. Use for general coding/quality/process rules that should apply regardless of the codebase.
- The two are NOT alternatives -- they cover different scopes. Cross-posting the same rule to both is acceptable when the rule is both KlodTalk-specific AND general.

## When to Use
- A user says "add this rule for the agents" without specifying scope.
- Reviewing a PR that adds a rule and choosing the right file.
- Auditing for duplication or drift between the two files.

## Decision Table

| Rule type | Place in | Why |
|-----------|----------|-----|
| KlodTalk file paths, broadcast filenames, three-place edit instinct | `CLAUDE.md` | KlodTalk-specific; meaningless on other projects. |
| Code quality (file size, dataclasses, error handling, naming) | `teams/roles/base.md` | Applies to every codebase. |
| Git commit/push policy | `teams/roles/base.md` | Universal process rule. |
| KlodTalk-specific architectural patterns (out_messages atomic write) | `CLAUDE.md` | Tied to KlodTalk server internals. |
| Pre-commit self-check (TODO/placeholder scan) | `teams/roles/base.md` | Universal. |
| Severity prefix taxonomy (`BLOCKER:` / `WARNING:` / `SUGGESTION:`) | `teams/roles/base.md` | Universal review convention. |

## Disambiguation Question
When unsure, ask: **"Would this rule make sense to an agent working on an unrelated Python or Kotlin codebase?"** If yes -> base.md. If no -> CLAUDE.md.

## Anti-Patterns
- Putting a universal coding rule in CLAUDE.md only -- agents on other projects never see it.
- Putting a KlodTalk-specific convention in base.md -- pollutes the universal file with cross-project noise.
- Maintaining two slightly different copies of the same rule -- pick one canonical home and reference it from the other.
