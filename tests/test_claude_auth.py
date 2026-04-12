"""Tests for Claude auth abstraction — works regardless of actual auth method."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.claude_auth.session import SessionAuth
from utils.claude_auth.api_key import ApiKeyAuth
from utils.claude_auth.base import ClaudeAuthBase


class TestSessionAuth:
    def test_get_cli_args_empty(self):
        auth = SessionAuth()
        assert auth.get_cli_args() == []

    def test_get_env_empty(self):
        auth = SessionAuth()
        assert auth.get_env() == {}

    def test_is_subclass(self):
        assert issubclass(SessionAuth, ClaudeAuthBase)

    def test_is_available_returns_bool(self):
        auth = SessionAuth()
        result = auth.is_available()
        assert isinstance(result, bool)

    def test_get_env_returns_dict(self):
        auth = SessionAuth()
        env = auth.get_env()
        assert isinstance(env, dict)

    def test_get_cli_args_returns_list(self):
        auth = SessionAuth()
        args = auth.get_cli_args()
        assert isinstance(args, list)


class TestApiKeyAuth:
    def test_available_when_env_set(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        auth = ApiKeyAuth()
        assert auth.is_available() is True

    def test_not_available_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        auth = ApiKeyAuth()
        assert auth.is_available() is False

    def test_get_env_returns_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        auth = ApiKeyAuth()
        env = auth.get_env()
        assert env["ANTHROPIC_API_KEY"] == "test-key-123"

    def test_get_env_empty_when_no_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        auth = ApiKeyAuth()
        assert auth.get_env() == {}

    def test_get_cli_args_empty(self):
        auth = ApiKeyAuth()
        assert auth.get_cli_args() == []

    def test_available_with_empty_string(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        auth = ApiKeyAuth()
        assert auth.is_available() is False

    def test_get_env_with_special_chars(self, monkeypatch):
        key = "sk-ant-api03-abc123/+="
        monkeypatch.setenv("ANTHROPIC_API_KEY", key)
        auth = ApiKeyAuth()
        assert auth.get_env()["ANTHROPIC_API_KEY"] == key

    def test_is_subclass(self):
        assert issubclass(ApiKeyAuth, ClaudeAuthBase)


class TestFactory:
    def test_factory_session(self):
        from utils.claude_auth import get_claude_auth
        auth = get_claude_auth("session")
        assert isinstance(auth, SessionAuth)

    def test_factory_api_key(self):
        from utils.claude_auth import get_claude_auth
        auth = get_claude_auth("api_key")
        assert isinstance(auth, ApiKeyAuth)

    def test_factory_unknown_raises(self):
        from utils.claude_auth import get_claude_auth
        with pytest.raises(ValueError, match="Unknown Claude auth method"):
            get_claude_auth("unknown_method")

    def test_factory_returns_correct_interface(self):
        from utils.claude_auth import get_claude_auth
        for method in ("session", "api_key"):
            auth = get_claude_auth(method)
            assert hasattr(auth, "get_cli_args")
            assert hasattr(auth, "is_available")
            assert hasattr(auth, "get_env")

    def test_factory_session_and_api_key_are_different(self):
        from utils.claude_auth import get_claude_auth
        session = get_claude_auth("session")
        api_key = get_claude_auth("api_key")
        assert type(session) != type(api_key)


class TestMockClaudeAuth:
    """Tests that the mock_claude_auth fixture works correctly."""

    def test_mock_auth_returns_mock_args(self, mock_claude_auth):
        assert mock_claude_auth.get_cli_args() == ["--mock"]

    def test_mock_auth_is_available(self, mock_claude_auth):
        assert mock_claude_auth.is_available() is True

    def test_mock_auth_env(self, mock_claude_auth):
        assert mock_claude_auth.get_env() == {"MOCK_AUTH": "1"}

    def test_mock_is_subclass(self, mock_claude_auth):
        assert isinstance(mock_claude_auth, ClaudeAuthBase)
