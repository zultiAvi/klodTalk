"""Shared fixtures for KlodTalk tests."""

import os
import subprocess
import sys

import pytest

# Make server modules importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a minimal workspace with .klodTalk structure."""
    for subdir in ("in_messages", "out_messages", "pr_messages", "history", "team/current"):
        (tmp_path / ".klodTalk" / subdir).mkdir(parents=True)
    return tmp_path


@pytest.fixture
def mock_claude_auth(monkeypatch):
    """Neutral mock that makes tests independent of actual auth method."""
    from utils.claude_auth.base import ClaudeAuthBase
    import utils.claude_auth as claude_auth_mod

    class MockAuth(ClaudeAuthBase):
        def get_cli_args(self):
            return ["--mock"]

        def is_available(self):
            return True

        def get_env(self):
            return {"MOCK_AUTH": "1"}

    mock = MockAuth()
    monkeypatch.setattr(
        claude_auth_mod,
        "get_claude_auth",
        lambda *a, **kw: mock,
    )
    return mock


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config directory with server_config.yaml."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "server_config.yaml"
    config_file.write_text(
        "server:\n  host: '0.0.0.0'\n  port: 3174\n  docker: true\n"
        "claude:\n  auth_method: 'session'\n"
        "git:\n  protocol: 'ssh'\n"
    )
    return config_dir


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess.run to prevent real system calls. Returns (calls_list, MockResult_class)."""
    calls = []

    class MockResult:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def mock_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)
    return calls, MockResult


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repository with one tracked file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(repo), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(repo), capture_output=True)
    tracked = repo / "tracked.txt"
    tracked.write_text("tracked content")
    subprocess.run(["git", "add", "tracked.txt"], cwd=str(repo), capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), capture_output=True)
    return repo
