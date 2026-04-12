"""Claude authentication abstraction layer."""

import os
import yaml

from .base import ClaudeAuthBase
from .session import SessionAuth
from .api_key import ApiKeyAuth

_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "server_config.yaml")
)


def _read_config() -> dict:
    try:
        with open(_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def get_claude_auth(method: str = None) -> ClaudeAuthBase:
    """Factory. method from config or auto-detect."""
    if method is None:
        method = _read_config().get("claude", {}).get("auth_method", "session")
    if method == "session":
        return SessionAuth()
    elif method == "api_key":
        return ApiKeyAuth()
    raise ValueError(f"Unknown Claude auth method: {method}")
