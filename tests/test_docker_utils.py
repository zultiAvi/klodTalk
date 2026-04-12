"""Tests for Docker utils abstraction (mocked — no real Docker needed)."""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.docker.local import LocalDockerUtils
from utils.docker.base import DockerUtilsBase


class TestLocalDockerUtils:
    def test_is_subclass(self):
        assert issubclass(LocalDockerUtils, DockerUtilsBase)

    def test_is_available_when_docker_works(self, monkeypatch):
        class MockResult:
            returncode = 0
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.is_available() is True

    def test_is_available_when_docker_fails(self, monkeypatch):
        class MockResult:
            returncode = 1
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.is_available() is False

    def test_is_available_when_docker_not_installed(self, monkeypatch):
        def raise_exc(*a, **kw):
            raise FileNotFoundError("docker not found")
        monkeypatch.setattr(subprocess, "run", raise_exc)

        utils = LocalDockerUtils()
        assert utils.is_available() is False

    def test_run_container_success(self, monkeypatch):
        calls = []
        class MockResult:
            returncode = 0
            stdout = ""
        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return MockResult()
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        result = utils.run_container(
            name="test-container",
            image="test-image",
            volumes=["-v", "/host:/container"],
            env_vars=["-e", "FOO=bar"],
        )
        assert result is True
        # First call removes existing container, second starts new one
        assert len(calls) == 2
        assert "rm" in calls[0]
        assert "run" in calls[1]

    def test_run_container_failure(self, monkeypatch):
        call_count = [0]
        class MockResultOk:
            returncode = 0
            stdout = ""
        class MockResultFail:
            returncode = 1
            stdout = ""
        def mock_run(cmd, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return MockResultOk()  # rm succeeds
            return MockResultFail()  # run fails
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        result = utils.run_container("c", "img", [], [])
        assert result is False

    def test_run_container_with_gpu_args(self, monkeypatch):
        calls = []
        class MockResult:
            returncode = 0
            stdout = ""
        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return MockResult()
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        utils.run_container("c", "img", [], [], gpu_args=["--gpus", "all"])
        # The run command should contain gpu args
        run_cmd = calls[1]
        assert "--gpus" in run_cmd
        assert "all" in run_cmd

    def test_run_container_with_user_args(self, monkeypatch):
        calls = []
        class MockResult:
            returncode = 0
            stdout = ""
        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return MockResult()
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        utils.run_container("c", "img", [], [], user_args=["--user", "1000:1000"])
        run_cmd = calls[1]
        assert "--user" in run_cmd

    def test_stop_container(self, monkeypatch):
        calls = []
        class MockResult:
            returncode = 0
        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return MockResult()
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        result = utils.stop_container("test-container")
        assert result is True
        assert "rm" in calls[0]
        assert "test-container" in calls[0]

    def test_exec_in_container(self, monkeypatch):
        class MockResult:
            returncode = 0
            stdout = "output"
            stderr = ""
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        code, stdout, stderr = utils.exec_in_container("c", ["ls", "-la"])
        assert code == 0
        assert stdout == "output"
        assert stderr == ""

    def test_exec_in_container_with_user(self, monkeypatch):
        calls = []
        class MockResult:
            returncode = 0
            stdout = ""
            stderr = ""
        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return MockResult()
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        utils.exec_in_container("c", ["cmd"], user="1000:1000")
        assert "--user" in calls[0]
        assert "1000:1000" in calls[0]

    def test_exec_in_container_with_env(self, monkeypatch):
        calls = []
        class MockResult:
            returncode = 0
            stdout = ""
            stderr = ""
        def mock_run(cmd, **kwargs):
            calls.append(cmd)
            return MockResult()
        monkeypatch.setattr(subprocess, "run", mock_run)

        utils = LocalDockerUtils()
        utils.exec_in_container("c", ["cmd"], env_vars=["FOO=bar", "BAZ=qux"])
        cmd = calls[0]
        assert "-e" in cmd
        assert "FOO=bar" in cmd
        assert "BAZ=qux" in cmd

    def test_image_exists_true(self, monkeypatch):
        class MockResult:
            returncode = 0
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.image_exists("test-image") is True

    def test_image_exists_false(self, monkeypatch):
        class MockResult:
            returncode = 1
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.image_exists("nonexistent") is False

    def test_is_container_running_true(self, monkeypatch):
        class MockResult:
            returncode = 0
            stdout = "true\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.is_container_running("c") is True

    def test_is_container_running_false(self, monkeypatch):
        class MockResult:
            returncode = 0
            stdout = "false\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.is_container_running("c") is False

    def test_is_container_running_not_found(self, monkeypatch):
        class MockResult:
            returncode = 1
            stdout = ""
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: MockResult())

        utils = LocalDockerUtils()
        assert utils.is_container_running("nonexistent") is False


class TestDockerFactory:
    def test_factory_returns_local(self):
        from utils.docker import get_docker_utils
        utils = get_docker_utils()
        assert isinstance(utils, LocalDockerUtils)

    def test_factory_returns_correct_interface(self):
        from utils.docker import get_docker_utils
        utils = get_docker_utils()
        assert hasattr(utils, "is_available")
        assert hasattr(utils, "run_container")
        assert hasattr(utils, "stop_container")
        assert hasattr(utils, "exec_in_container")
        assert hasattr(utils, "image_exists")
        assert hasattr(utils, "is_container_running")
