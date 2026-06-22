---
skill_name: skills-spec-conformance
triggers:
  - Writing or auditing a KlodTalk skill and needing to know which official Agent Skills spec fields apply
  - A future CLI release tightens skill loading and you must check KlodTalk's frontmatter against the canonical spec
  - Deciding whether a KlodTalk-specific frontmatter key (skill_name, triggers, summary) maps to an official one
summary: "Field-by-field map of the official Agent Skills spec (agentskills.io/specification) onto KlodTalk's existing CLAUDE/skills frontmatter: which official keys KlodTalk uses, renames, omits, and the single-file-vs-directory structural difference."
---

# Skill: Skills Spec Conformance

## Quick Reference
- Canonical spec: https://agentskills.io/specification (was `anthropics/skills/blob/main/spec/agent-skills-spec.md`, now redirects there).
- Official **required** frontmatter: `name`, `description`. Official **optional**: `license`, `compatibility`, `metadata`, `allowed-tools` (experimental).
- KlodTalk frontmatter: `skill_name`, `triggers`, `summary` — a stricter superset of the *intent*, but **different key names**.
- Structural gap: official = a `skill-name/SKILL.md` **directory**; KlodTalk = a flat single `kebab-case.md` file in `CLAUDE/skills/`.

## When to Use
Use when authoring/auditing a KlodTalk skill, or when a CLI release tightens skill loading and you need to confirm KlodTalk's pattern still parses. `skill-creator.md` is the entry point; this doc is the conformance reference it links to.

## Instructions

### Field-by-field map (official → KlodTalk)
| Official key | Req? | KlodTalk equivalent | Notes |
|---|---|---|---|
| `name` (≤64 chars, `[a-z0-9-]`, no leading/trailing/double hyphen, == dir name) | yes | `skill_name` (kebab-case, == **filename stem**) | Same rules; KlodTalk renames the key and anchors on file stem since it has no per-skill dir. |
| `description` (≤1024 chars, what + when) | yes | `summary` (double-quoted; colons must be quoted) + `triggers` (2–5 observable events) | KlodTalk **splits** description into a one-line `summary` and a `triggers` list. |
| `license` | no | omitted | Repo-level license covers all skills. |
| `compatibility` (≤500) | no | omitted (stated in body, e.g. "CLI v2.1.181+") | Optional; KlodTalk states env/version floors in prose instead. |
| `metadata` (str map) | no | omitted | No author/version tracking per skill. |
| `allowed-tools` | no | omitted (experimental) | Do NOT add as a control — deny/allow rules are NO-OPs in KlodTalk. |

### Conformance rules for new KlodTalk skills
- Keep `skill_name` to the official `name` charset (lowercase alphanum + single hyphens, no leading/trailing/`--`).
- Keep the full file well under the spec's "≤500 lines / <5000 tokens" guidance — KlodTalk's own cap is 50 lines.
- KlodTalk does NOT migrate to `SKILL.md` directories; the flat-file convention is intentional. If the CLI ever requires `name`/`description`, add them as aliases rather than renaming.

## Cross-References
- `skill-creator.md` — required-fields checklist and the increment rule; links here for the official mapping.

## Source Attribution
- `anthropics/skills` (official Anthropic): https://github.com/anthropics/skills — ~154k stars. Canonical spec now hosted at https://agentskills.io/specification.
