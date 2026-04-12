"""Abstract base class for Claude authentication methods."""

from abc import ABC, abstractmethod


class ClaudeAuthBase(ABC):
    @abstractmethod
    def get_cli_args(self) -> list[str]:
        """Return extra CLI arguments for the claude command."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this auth method is configured and available."""

    @abstractmethod
    def get_env(self) -> dict:
        """Return environment variables needed for this auth method."""
