---
skill_name: role-inheritance-pattern
triggers:
  - Authoring a new file under teams/roles/
  - Editing teams/roles/base.md
  - Reviewing a role file for duplicated base content
summary: Use the `<!-- inherits: base.md -->` HTML comment in every role file so shared conventions (pre-commit checks, severity prefixes, git rules, output file paths) live once in teams/roles/base.md and stay in sync across roles.
---

# Skill: Role Inheritance Pattern (`base.md` Convention)

## Quick Reference
- Every role file in `teams/roles/` should contain `<!-- inherits: base.md -->` (HTML comment) near the top of the body.
- Shared conventions live in `teams/roles/base.md`. Role files reference them ("See **base.md** for ...") rather than copying them.
- The orchestrator includes `base.md` content when composing the role prompt at runtime, so inherited rules are always in effect.

## When to Use
- Creating any new role under `teams/roles/`.
- Editing an existing role and noticing it duplicates a section from `base.md`.
- Updating a cross-role convention -- edit `base.md`, not each role.

## What Belongs Where

| Lives in `base.md` (shared) | Lives in `<role>.md` (role-specific) |
|-----------------------------|--------------------------------------|
| Pre-commit self-check (TODO/FIXME/placeholder scan) | Role responsibilities and pipeline position |
| Issue severity prefixes (`BLOCKER:` / `WARNING:` / `SUGGESTION:`) | Required output file format and final-verdict tokens |
| Git commit rules (descriptive message, do not push) | Domain-specific checks (e.g., test pass/fail tokens for the reviewer) |
| Output file path convention (`/workspace/.klodTalk/team/current/<role>_output.txt`) | Tool restrictions via `disallowedTools` frontmatter |
| Stub & placeholder detection list | When-to-block vs when-to-warn rules unique to the role |
| Results-folder routing for external artifacts | Review-fix-loop or retry semantics specific to the role |

## Instructions for New Role Authors

1. Start by copying the structure of an existing role file (e.g., `teams/roles/coder.md` or `teams/roles/reviewer.md`).
2. Place `<!-- inherits: base.md -->` near the top of the body (after any YAML frontmatter).
3. For every section you are about to write, ask: "Is this rule already in `base.md`?" If yes, reference it ("See **base.md** for ...") instead of copying.
4. Keep only role-unique content in the new file: the role's responsibilities, its required output format, and any domain-specific checks.
5. If you find yourself wanting to change something in `base.md` for one role only, that is a signal the rule belongs in the role file -- not a signal to copy `base.md` and tweak it.

## Examples in This Repo
- `teams/roles/reviewer.md` -- inherits, then references `base.md` for severity prefixes and stub detection.
- `teams/roles/coder.md` -- inherits, then defines only the coder-specific output and review-fix protocol.
- `teams/roles/base.md` -- the canonical shared rules.

## Anti-Patterns
- Copy-pasting the severity prefix table into every role file -- when `base.md` updates, the copies drift.
- Adding role-specific exceptions inside `base.md` -- pollutes the shared file with conditionals.
- Omitting `<!-- inherits: base.md -->` and silently relying on the orchestrator -- the comment is the explicit, reviewable marker.

## Related
- `skill-overrides-per-role` -- per-role overrides for skill activation, complementary to base-content inheritance.

## Source
bobmatnyc/claude-mpm -- https://github.com/bobmatnyc/claude-mpm
