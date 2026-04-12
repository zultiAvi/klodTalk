"""Linux OS utilities implementation."""

import os
import shutil
from typing import Optional

from .base import OsUtilsBase


class LinuxOsUtils(OsUtilsBase):
    def get_platform(self) -> str:
        return "linux"

    def get_user_ids(self) -> tuple[Optional[int], Optional[int]]:
        return os.getuid(), os.getgid()

    def which(self, cmd: str) -> Optional[str]:
        return shutil.which(cmd)
