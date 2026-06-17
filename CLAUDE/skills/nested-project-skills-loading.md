---
skill_name: nested-project-skills-loading
triggers:
  - Deciding where a project-specific skill should live (global vs per-project)
  - Working under a subtree (e.g. Air2Road) that ships its own .claude/skills
  - A skill name clashes between the global set and a project's nested set
summary: "Claude Code (>= 2.1.178) auto-loads nested `.claude/skills` dirs when working in that subtree; on a name clash the nested skill is exposed as `<dir>:<name>` so both stay available. Keep cross-project skills in CLAUDE/skills/, push project-specific ones into that project's nested .claude/skills."
---

# Skill: Nested Per-Project `.claude/skills` Directory-Qualified Loading

## Quick Reference
- A `.claude/skills/` directory nested under a subtree **auto-loads** when the session is
  working on files in that subtree (cwd / edited-file path), in addition to the
  top-level `/workspace/.claude/skills` (and KlodTalk's `CLAUDE/skills/`).
- **Name clash:** if a nested skill shares a name with a global one, the nested skill is
  exposed as `<dir>:<name>` (directory-qualified) so **both remain invokable** — the
  nested one does not silently shadow the global one.
- Requires Claude Code **>= 2.1.178** (KlodTalk floor — see `required-minimum-version-pin.md`).

## The 2.1.178 Fix (why the floor matters here)
Before 2.1.178, nested directory-qualified skills could be **blocked by a permission
prompt** when invoked — fine interactively, fatal in non-interactive `--print`/`-p` runs
(which is exactly how KlodTalk runs every agent in Docker). 2.1.178 lets the qualified
`<dir>:<name>` form resolve without an interactive prompt, so nested per-project skills
are now safe under KlodTalk's non-interactive runtime. Do not rely on this below 2.1.178.

## KlodTalk Guidance
- **Cross-project / harness skills → `CLAUDE/skills/`** (the global ~80-skill surface every
  role sees). This is the default home for anything reusable across projects.
- **Project-specific skills → that project's nested `.claude/skills/`.** Example: Air2Road
  already keeps its skills in `Air2Road/CLAUDE/skills/`; a nested `Air2Road/.claude/skills/`
  would auto-load only while an agent is working inside that subtree, cutting global
  skill-surface noise for unrelated sessions.
- This is a placement convention, not a runtime change — no Dockerfile or server edits.

## Cross-References
- `required-minimum-version-pin.md` — the 2.1.178 floor that makes non-interactive nested
  loading safe.
- `disable-bundled-skills.md` — complementary surface-pruning (removes bundled built-ins);
  this skill instead scopes *KlodTalk* skills to the subtree that needs them.

## Source
- anthropics/claude-code v2.1.178 (github.com/anthropics/claude-code, 80,000+ stars) —
  https://github.com/anthropics/claude-code/releases/tag/v2.1.178
