"""Local Docker CLI implementation (currently working)."""

import subprocess
from typing import Optional

from .base import DockerUtilsBase


class LocalDockerUtils(DockerUtilsBase):
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

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
        # Remove any existing container with same name
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)

        cmd = [
            "docker", "run", "-d",
            "--name", name,
            *(network_args or []),
            *(user_args or []),
            *(gpu_args or []),
            *env_vars,
            *volumes,
            image,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def stop_container(self, name: str) -> bool:
        result = subprocess.run(
            ["docker", "rm", "-f", name], capture_output=True,
        )
        return result.returncode == 0

    def exec_in_container(
        self,
        name: str,
        command: list[str],
        env_vars: list[str] = None,
        user: Optional[str] = None,
    ) -> tuple[int, str, str]:
        cmd = ["docker", "exec"]
        if user:
            cmd += ["--user", user]
        for env in (env_vars or []):
            cmd += ["-e", env]
        cmd.append(name)
        cmd.extend(command)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def image_exists(self, image_name: str) -> bool:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name], capture_output=True,
        )
        return result.returncode == 0

    def is_container_running(self, name: str) -> bool:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", name],
            capture_output=True, text=True,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"

    def commit_container(self, container_name: str, image_name: str) -> bool:
        result = subprocess.run(
            ["docker", "commit", container_name, image_name],
            capture_output=True, text=True,
        )
        return result.returncode == 0

    def get_image_size(self, image_name: str) -> Optional[int]:
        result = subprocess.run(
            ["docker", "image", "inspect", "--format", "{{.Size}}", image_name],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return None
        try:
            return int(result.stdout.strip())
        except ValueError:
            return None
