"""Abstract base class for Git protocol utilities."""

from abc import ABC, abstractmethod


class GitUtilsBase(ABC):
    @abstractmethod
    def get_protocol(self) -> str:
        """Return protocol name (e.g. 'ssh', 'https')."""

    @abstractmethod
    def test_connection(self, remote_url: str) -> bool:
        """Test if the remote is reachable with this protocol."""

    @abstractmethod
    def configure_remote(self, repo_path: str, remote_url: str) -> None:
        """Configure the remote URL for a repo."""
