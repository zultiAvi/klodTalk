"""Abstract base class for Docker utilities."""

from abc import ABC, abstractmethod
from typing import Optional


class DockerUtilsBase(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if Docker is available and running."""

    @abstractmethod
    def run_container(
        self,
        name: str,
        image: str,
        volumes: list[str],
        env_vars: list[str],
        user_args: list[str] = None,
        gpu_args: list[str] = None,
        network_args: list[str] = None,
    ) -> bool:
        """Start a detached container. Returns True on success."""

    @abstractmethod
    def stop_container(self, name: str) -> bool:
        """Stop and remove a container. Returns True on success."""

    @abstractmethod
    def exec_in_container(
        self,
        name: str,
        command: list[str],
        env_vars: list[str] = None,
        user: Optional[str] = None,
    ) -> tuple[int, str, str]:
        """Execute a command in a running container. Returns (exit_code, stdout, stderr)."""

    @abstractmethod
    def image_exists(self, image_name: str) -> bool:
        """Check if a Docker image exists locally."""

    @abstractmethod
    def is_container_running(self, name: str) -> bool:
        """Check if a container is running."""

    @abstractmethod
    def commit_container(self, container_name: str, image_name: str) -> bool:
        """Commit a running container as a new image. Returns True on success."""

    @abstractmethod
    def copy_from_container(self, container_name: str, container_path: str, host_path: str) -> bool:
        """Copy a file or directory from a container to the host. Returns True on success."""

    @abstractmethod
    def get_image_size(self, image_name: str) -> Optional[int]:
        """Return the image size in bytes, or None if image not found."""
