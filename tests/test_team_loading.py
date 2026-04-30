"""Tests for team loading after migration from JSON configs to .md claude teams."""

import os
import sys

import pytest

# Make server modules importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


# ── 1. TEAMS_DIR points to teams/teams (not teams/configs) ──────────────────

def test_teams_dir_points_to_md_folder():
    import server
    assert server.TEAMS_DIR.endswith(os.path.join("teams", "teams")), (
        f"TEAMS_DIR should end with 'teams/teams', got: {server.TEAMS_DIR}"
    )


# ── 2. get_available_teams reads .md files ──────────────────────────────────

def test_get_available_teams_reads_md_files():
    import server
    teams = server.get_available_teams()
    assert isinstance(teams, list)
    # There should be at least one team (tdd.md exists)
    assert len(teams) > 0
    # All names should be strings (from .md basenames)
    for t in teams:
        assert "name" in t
        assert isinstance(t["name"], str)


# ── 3. load_team returns name for .md team ──────────────────────────────────

def test_load_team_returns_name_for_md_team():
    import server
    result = server.load_team("tdd")
    assert isinstance(result, dict)
    assert result.get("name") == "tdd"


# ── 4. load_team returns empty for missing team ─────────────────────────────

def test_load_team_returns_empty_for_missing_team():
    import server
    result = server.load_team("nonexistent_team_xyz")
    assert result == {}


# ── 5. No TEAM_ORCHESTRATOR in server.py ─────────────────────────────────────

def test_no_team_orchestrator_in_server():
    server_path = os.path.join(BASE_DIR, "server", "server.py")
    with open(server_path) as f:
        content = f.read()
    assert "TEAM_ORCHESTRATOR" not in content, (
        "server.py should not contain TEAM_ORCHESTRATOR"
    )


# ── 6. No TEAM_ORCHESTRATOR in run_agent.sh ──────────────────────────────────

def test_no_team_orchestrator_in_run_agent_sh():
    sh_path = os.path.join(BASE_DIR, "server", "run_agent.sh")
    with open(sh_path) as f:
        content = f.read()
    assert "TEAM_ORCHESTRATOR" not in content, (
        "run_agent.sh should not contain TEAM_ORCHESTRATOR"
    )


# ── 7. No TEAM_ORCHESTRATOR in run_agent.py ──────────────────────────────────

def test_no_team_orchestrator_in_run_agent_py():
    py_path = os.path.join(BASE_DIR, "server", "run_agent.py")
    with open(py_path) as f:
        content = f.read()
    assert "TEAM_ORCHESTRATOR" not in content, (
        "run_agent.py should not contain TEAM_ORCHESTRATOR"
    )


# ── 8. No configs/ directory exists ──────────────────────────────────────────

def test_no_configs_dir_exists():
    configs_dir = os.path.join(BASE_DIR, "teams", "configs")
    assert not os.path.isdir(configs_dir), (
        f"teams/configs/ should not exist, found: {configs_dir}"
    )


# ── 9. No operations/ directory exists ───────────────────────────────────────

def test_no_operations_dir_exists():
    ops_dir = os.path.join(BASE_DIR, "teams", "operations")
    assert not os.path.isdir(ops_dir), (
        f"teams/operations/ should not exist, found: {ops_dir}"
    )


# ── 10. Claude team script at correct path ───────────────────────────────────

def test_claude_team_script_at_correct_path():
    script = os.path.join(BASE_DIR, "teams", "run_claude_team.sh")
    assert os.path.isfile(script), (
        f"teams/run_claude_team.sh should exist at: {script}"
    )


# ── 11. Team .md files exist in teams/teams/ ─────────────────────────────────

def test_team_md_files_exist():
    teams_dir = os.path.join(BASE_DIR, "teams", "teams")
    expected = ["tdd.md", "plan-code-review.md", "plan-code.md"]
    for name in expected:
        path = os.path.join(teams_dir, name)
        assert os.path.isfile(path), (
            f"Expected team file at: {path}"
        )


# ── 12. add_team doc has no JSON references ──────────────────────────────────

def test_add_team_doc_no_json_references():
    doc_path = os.path.join(BASE_DIR, "docs", "add_team.md")
    with open(doc_path) as f:
        content = f.read()
    assert "configs/" not in content, (
        "docs/add_team.md should not reference 'configs/'"
    )
    # Team files should not be referenced as .json (agents.json is OK)
    assert "my-team.json" not in content, (
        "docs/add_team.md should not reference team files as .json"
    )
    assert "teams/configs" not in content, (
        "docs/add_team.md should not reference teams/configs"
    )


# ── 13. Description extracted from .md ────────────────────────────────────────

def test_description_extracted_from_md():
    import server
    teams = server.get_available_teams()
    # At least one team should have a non-empty description
    has_description = any(t.get("description") for t in teams)
    assert has_description, (
        "At least one team should have a description extracted from .md"
    )


# ── 14. load_team detects `## disabled` heading ──────────────────────────────

def test_load_team_detects_disabled_flag(tmp_path, monkeypatch):
    import server
    monkeypatch.setattr(server, "TEAMS_DIR", str(tmp_path))
    (tmp_path / "team_x.md").write_text(
        "# Team X\nA short description.\n\n## disabled\n\n## Members\n"
    )
    result = server.load_team("team_x")
    assert result.get("disabled") is True


# ── 15. get_available_teams excludes disabled teams ──────────────────────────

def test_get_available_teams_excludes_disabled(tmp_path, monkeypatch):
    import server
    monkeypatch.setattr(server, "TEAMS_DIR", str(tmp_path))
    (tmp_path / "enabled.md").write_text(
        "# Enabled\nA live team.\n\n## enabled\n\n## Members\n"
    )
    (tmp_path / "disabled.md").write_text(
        "# Disabled\nShould not be listed.\n\n## disabled\n\n## Members\n"
    )
    teams = server.get_available_teams()
    names = [t["name"] for t in teams]
    assert "enabled" in names
    assert "disabled" not in names


# ── 16. disabled heading is not consumed as the description ──────────────────

def test_load_team_disabled_does_not_eat_description(tmp_path, monkeypatch):
    import server
    monkeypatch.setattr(server, "TEAMS_DIR", str(tmp_path))
    (tmp_path / "team_y.md").write_text(
        "# Team Y\nThis is the real description.\n\n## disabled\n\n## Members\n"
    )
    result = server.load_team("team_y")
    assert result.get("disabled") is True
    assert result.get("description") == "This is the real description."
    assert "disabled" not in result.get("description", "").lower()


# ── 17. missing state heading is treated as disabled ─────────────────────────

def test_load_team_missing_state_heading_is_disabled(tmp_path, monkeypatch, caplog):
    import logging
    import server
    monkeypatch.setattr(server, "TEAMS_DIR", str(tmp_path))
    (tmp_path / "team_z.md").write_text(
        "# Team Z\nA description without state heading.\n\n## Members\n"
    )
    with caplog.at_level(logging.WARNING):
        result = server.load_team("team_z")
    assert result.get("disabled") is True
    assert any(
        "missing mandatory" in record.message and "team_z" in record.message
        for record in caplog.records
    )
