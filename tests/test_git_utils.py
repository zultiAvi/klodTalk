"""Tests for Git utils abstraction."""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.git.ssh import SshGitUtils
from utils.git.https import HttpsGitUtils
from utils.git.base import GitUtilsBase


class TestSshGitUtils:
    def test_get_protocol(self):
        utils = SshGitUtils()
        assert utils.get_protocol() == "ssh"

    def test_is_subclass(self):
        assert issubclass(SshGitUtils, GitUtilsBase)

    def test_test_connection_with_mock(self, monkeypatch):
        """Test connection check with mocked subprocess to avoid real network calls."""
        class MockResult:
            returncode = 0

        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())
        utils = SshGitUtils()
        assert utils.test_connection("git@github.com:user/repo.git") is True

    def test_test_connection_failure_with_mock(self, monkeypatch):
        class MockResult:
            returncode = 128

        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())
        utils = SshGitUtils()
        assert utils.test_connection("git@github.com:user/repo.git") is False

    def test_test_connection_exception(self, monkeypatch):
        def raise_error(*a, **kw):
            raise OSError("no git")

        monkeypatch.setattr(subprocess, "run", raise_error)
        utils = SshGitUtils()
        assert utils.test_connection("git@github.com:user/repo.git") is False

    def test_configure_remote_calls_git(self, monkeypatch):
        calls = []

        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            class R:
                returncode = 0
            return R()

        monkeypatch.setattr(subprocess, "run", mock_run)
        utils = SshGitUtils()
        utils.configure_remote("/tmp/repo", "git@github.com:user/repo.git")

        assert len(calls) == 1
        assert "set-url" in calls[0]
        assert "origin" in calls[0]


class TestHttpsGitUtils:
    def test_get_protocol(self):
        utils = HttpsGitUtils()
        assert utils.get_protocol() == "https"

    def test_is_subclass(self):
        assert issubclass(HttpsGitUtils, GitUtilsBase)

    def test_not_implemented(self):
        utils = HttpsGitUtils()
        with pytest.raises(NotImplementedError):
            utils.test_connection("https://example.com/repo.git")
        with pytest.raises(NotImplementedError):
            utils.configure_remote("/tmp/repo", "https://example.com/repo.git")


class TestFactory:
    def test_factory_ssh(self):
        from utils.git import get_git_utils
        utils = get_git_utils("ssh")
        assert isinstance(utils, SshGitUtils)

    def test_factory_https(self):
        from utils.git import get_git_utils
        utils = get_git_utils("https")
        assert isinstance(utils, HttpsGitUtils)

    def test_factory_unknown_raises(self):
        from utils.git import get_git_utils
        with pytest.raises(ValueError):
            get_git_utils("ftp")

    def test_factory_returns_correct_interface(self):
        from utils.git import get_git_utils
        for protocol in ("ssh", "https"):
            utils = get_git_utils(protocol)
            assert hasattr(utils, "get_protocol")
            assert hasattr(utils, "test_connection")
            assert hasattr(utils, "configure_remote")
