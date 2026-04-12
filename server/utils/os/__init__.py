"""OS abstraction layer."""

import platform

from .base import OsUtilsBase
from .linux import LinuxOsUtils


def get_os_utils() -> OsUtilsBase:
    """Factory: return OS utils for the current platform."""
    system = platform.system()
    if system == "Linux":
        return LinuxOsUtils()
    # Future: add WindowsOsUtils, MacOsUtils
    raise NotImplementedError(f"OS utils not implemented for {system}")
