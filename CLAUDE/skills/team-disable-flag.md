---
skill_name: team-disable-flag
triggers:
  - Adding, editing, or listing teams in `teams/teams/`
  - Hiding a team from the client dropdown without deleting the file
  - Modifying `load_team()` or `get_available_teams()` in `server/server.py`
summary: Every team `.md` must contain a mandatory `## enabled` or `## disabled` H2 heading; `## disabled` (or a missing heading) hides the team from `get_available_teams()`.
---

# Skill: Team Disable Flag

The term "flag" in the skill name is historical — the mechanism is now an H2 markdown heading, not a `key: value` line.

## Quick Reference
- Mandatory: every team `.md` file in `teams/teams/` MUST contain exactly one of `## enabled` or `## disabled` as an H2 heading.
- Allowed values: exactly `## enabled` or `## disabled` (case-insensitive after trimming whitespace). No other variants are recognized.
- Placement: after the team's one-line description, before the `## Members` section. Body under the heading is empty.
- Missing heading → the team is treated as **disabled** and a warning is logged. There is no default; you must declare the state explicitly.
- Canonical disabled examples: `teams/teams/plan-code-qa-review.md` and `teams/teams/plan-code-review-execute.md`.

## When to Use
When you need to hide a team from the client's team dropdown without deleting its `.md` file, when authoring a new team file (you must add the heading), or when modifying the team enumeration code paths.

## Instructions

### Authoring a team file
The minimum structure of a team `.md` file is:

```markdown
# Team: <Display Name>

<one-line description>

## enabled

## Members

| Name | Role | Model |
|------|------|-------|
| ... | ... | ... |
```

Replace `## enabled` with `## disabled` to hide the team from the dropdown.

### Disabling an existing team
Open `teams/teams/<name>.md` and change the `## enabled` heading to `## disabled`. No other change is required. Re-enable by changing it back.

### Code paths to know
- `load_team(team_name)` in `server/server.py` — single-pass parser. Tracks a `state_heading` variable as it scans the file. A line whose trimmed lowercased form equals `## enabled` or `## disabled` sets the heading; the heading line is **never** picked up as the team description. After the loop, if no state heading was found, `log.warning(...)` is emitted and `disabled=True` is returned. Otherwise `disabled = (state_heading == "disabled")`. Returns `{"name", "display_name", "description", "disabled"}`.
- `get_available_teams()` in `server/server.py` — filters out entries where `data.get("disabled")` is truthy and exposes `{"name", "description"}` only, so the `disabled` key never leaks to the client.

### Testing pattern
Tests in `tests/test_team_loading.py` use `tmp_path` + `monkeypatch.setattr(server, "TEAMS_DIR", str(tmp_path))` to isolate from the real `teams/teams/` folder. Fixture `.md` files MUST include either `## enabled` or `## disabled` (or deliberately omit it to test the missing-heading path).

### Known scope boundary
The session-start path (`project.get("team")` in `server/server.py:612-625`) bypasses `load_team()` and `get_available_teams()`, so a project configured with a disabled team can still launch it. The `## disabled` heading only affects the dropdown, not project-pinned teams. Treat this as a deliberate scope boundary unless explicitly extended.
