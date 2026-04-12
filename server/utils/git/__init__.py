"""Git protocol abstraction layer."""

import os
import yaml

from .base import GitUtilsBase
from .ssh import SshGitUtils
from .https import HttpsGitUtils

_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "server_config.yaml")
)


def _read_config() -> dict:
    try:
        with open(_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def get_git_utils(protocol: str = None) -> GitUtilsBase:
    """Factory: return git utils for the configured protocol."""
    if protocol is None:
        protocol = _read_config().get("git", {}).get("protocol", "ssh")
    if protocol == "ssh":
        return SshGitUtils()
    elif protocol == "https":
        return HttpsGitUtils()
    raise ValueError(f"Unknown git protocol: {protocol}")
