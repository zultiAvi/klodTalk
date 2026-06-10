# Skill: Team Member Model Column — Who Consumes It

## When to Use
Authoring or editing a team `.md` Members table, choosing a model for a member, or
debugging why a member's model value seems ignored. Especially when using a full model ID
(e.g. `claude-fable-5`) instead of an `opus`/`sonnet`/`haiku` shorthand.

## Instructions

The `Model` column in a `teams/teams/*.md` Members table is consumed ONLY by the
orchestrator (the Claude instance reading the team) when it spawns each member via the
Agent tool. It is NOT parsed by:
- `teams/run_claude_team.sh` — its Members-table parser extracts only the **Role** column
  (awk `$3`); the Model column is never read. The shell only resolves `CLAUDE_MODEL` (the
  orchestrator's own model), defaulting to `claude-opus-4-8`.
- `server/server.py:load_team` — parses only name, description, and the `## enabled` /
  `## disabled` state. The Model column is untouched.

Implications:
- Full model IDs (`claude-fable-5`, `claude-mythos-5`) are valid in the Model column and
  document intent. They are NOT wired as shorthands — `opus` still resolves to Opus 4.8.
  Adding a new shorthand would require editing `CURRENT_MODELS` (server.py) + the alias
  resolution in `run_claude_team.sh` + widening the `_query_latest_model` validation regex.
- For single-agent "solo" teams, the actual runtime model is the orchestrator's
  `CLAUDE_MODEL`; the member Model column primarily documents which model the solo agent
  is meant to use. To force a solo team onto a specific model, set `CLAUDE_MODEL` to the
  full ID.

## Related
- `model-version-hygiene.md` — current/retired model IDs and shorthand resolution.
- `three-tier-model-routing.md` — which tier to pick per role.
- `team-disable-flag.md` — the `## enabled` / `## disabled` heading load_team parses.
