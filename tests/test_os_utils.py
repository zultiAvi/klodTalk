"""Tests for OS utils abstraction."""

import os
import sys
import platform

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.os.linux import LinuxOsUtils
from utils.os.base import OsUtilsBase


class TestLinuxOsUtils:
    def test_get_platform(self):
        utils = LinuxOsUtils()
        assert utils.get_platform() == "linux"

    def test_get_user_ids(self):
        utils = LinuxOsUtils()
        uid, gid = utils.get_user_ids()
        if platform.system() == "Linux":
            assert isinstance(uid, int)
            assert isinstance(gid, int)
            assert uid >= 0
            assert gid >= 0

    def test_which_python(self):
        utils = LinuxOsUtils()
        result = utils.which("python3")
        if platform.system() == "Linux":
            assert result is not None
            assert "python3" in result

    def test_which_nonexistent(self):
        utils = LinuxOsUtils()
        result = utils.which("nonexistent_command_xyz_12345")
        assert result is None

    def test_is_subclass(self):
        assert issubclass(LinuxOsUtils, OsUtilsBase)

    def test_which_returns_string_or_none(self):
        utils = LinuxOsUtils()
        result = utils.which("ls")
        if result is not None:
            assert isinstance(result, str)

    def test_which_git(self):
        utils = LinuxOsUtils()
        result = utils.which("git")
        if platform.system() == "Linux":
            assert result is not None

    def test_user_ids_match_os_module(self):
        if platform.system() != "Linux":
            return
        utils = LinuxOsUtils()
        uid, gid = utils.get_user_ids()
        assert uid == os.getuid()
        assert gid == os.getgid()


class TestFactory:
    def test_get_os_utils_on_linux(self):
        if platform.system() != "Linux":
            return
        from utils.os import get_os_utils
        utils = get_os_utils()
        assert isinstance(utils, LinuxOsUtils)

    def test_factory_returns_correct_interface(self):
        if platform.system() != "Linux":
            return
        from utils.os import get_os_utils
        utils = get_os_utils()
        assert hasattr(utils, "get_platform")
        assert hasattr(utils, "get_user_ids")
        assert hasattr(utils, "which")
