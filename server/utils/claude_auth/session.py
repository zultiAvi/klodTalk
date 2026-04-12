"""OAuth/session-based Claude authentication (currently working)."""

from pathlib import Path

from .base import ClaudeAuthBase


class SessionAuth(ClaudeAuthBase):
    """Uses ~/.claude OAuth session tokens. No extra CLI args needed."""

    def get_cli_args(self) -> list[str]:
        return []

    def is_available(self) -> bool:
        return Path("~/.claude").expanduser().is_dir()

    def get_env(self) -> dict:
        return {}
