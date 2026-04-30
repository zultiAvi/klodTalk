---
skill_name: team-disable-flag
triggers:
  - Adding, editing, or listing teams in `teams/teams/`
  - Hiding a team from the client dropdown without deleting the file
  - Modifying `load_team()` or `get_available_teams()` in `server/server.py`
summary: Add `disabled: true` to a team `.md` to hide it from `get_available_teams()`; parsed by `load_team()`.
---

# Skill: Team Disable Flag

## Quick Reference
- Flag: a line `disabled: true` anywhere in `teams/teams/<name>.md`
- Accepts: `true`, `yes`, `1` (case-insensitive); optional leading `#` so a commented `# disabled: true` works
- Re-enable: remove the line or set `disabled: false`

## When to Use
When you need to hide a team from the client's team dropdown without deleting its `.md` file, or when modifying the team enumeration code paths.

## Instructions

### Disabling a team (user perspective)
Add a single line to the team's `.md` file:

```
disabled: true
```

The line can sit anywhere in the file. The server's `load_team()` parses it and `get_available_teams()` filters disabled teams out before the client receives the team list. No client change is needed.

### Code paths to know
- `load_team(team_name)` in `server/server.py` — parses the flag in a single pass over the file's lines. Skips the `disabled:` line when extracting the description, so a real description on a later line is still picked up. Returns `disabled` in the dict alongside `name`, `display_name`, `description`.
- `get_available_teams()` in `server/server.py` — filters `data.get("disabled")` truthy entries; returns only `{"name", "description"}` to callers, so the `disabled` key does not leak into the client payload.

### Testing pattern
Tests in `tests/test_team_loading.py` use `tmp_path` + `monkeypatch.setattr(server, "TEAMS_DIR", str(tmp_path))` to isolate from the real `teams/teams/` folder. Any new flag-related tests must follow the same isolation pattern.

### Known gap (follow-up)
The session-start path (`project.get("team")` in `server/server.py:612-625`) bypasses `load_team()` and `get_available_teams()`, so a project configured with a disabled team can still launch it. The disable flag only affects the dropdown, not project-pinned teams. Treat this as a deliberate scope boundary unless explicitly extended.
