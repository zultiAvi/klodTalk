"""Docker abstraction layer."""

from .base import DockerUtilsBase
from .local import LocalDockerUtils


def get_docker_utils() -> DockerUtilsBase:
    """Factory: return Docker utils (only local for now)."""
    return LocalDockerUtils()
