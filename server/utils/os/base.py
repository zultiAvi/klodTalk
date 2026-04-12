"""Abstract base class for OS utilities."""

from abc import ABC, abstractmethod
from typing import Optional


class OsUtilsBase(ABC):
    @abstractmethod
    def get_platform(self) -> str:
        """Return platform name (e.g. 'linux', 'windows', 'darwin')."""

    @abstractmethod
    def get_user_ids(self) -> tuple[Optional[int], Optional[int]]:
        """Return (uid, gid) or (None, None) on platforms without them."""

    @abstractmethod
    def which(self, cmd: str) -> Optional[str]:
        """Find executable in PATH. Returns path or None."""
