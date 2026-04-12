"""API key-based Claude authentication."""

import os

from .base import ClaudeAuthBase


class ApiKeyAuth(ClaudeAuthBase):
    """Uses ANTHROPIC_API_KEY environment variable."""

    def get_cli_args(self) -> list[str]:
        return []

    def is_available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def get_env(self) -> dict:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        return {"ANTHROPIC_API_KEY": key} if key else {}
