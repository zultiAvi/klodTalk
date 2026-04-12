"""SSH git protocol implementation (currently working)."""

import subprocess

from .base import GitUtilsBase


class SshGitUtils(GitUtilsBase):
    def get_protocol(self) -> str:
        return "ssh"

    def test_connection(self, remote_url: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--exit-code", remote_url],
                capture_output=True, timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def configure_remote(self, repo_path: str, remote_url: str) -> None:
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote_url],
            cwd=repo_path, capture_output=True,
        )
