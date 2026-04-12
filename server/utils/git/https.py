"""HTTPS git protocol implementation (stub — not yet fully implemented)."""

from .base import GitUtilsBase


class HttpsGitUtils(GitUtilsBase):
    def get_protocol(self) -> str:
        return "https"

    def test_connection(self, remote_url: str) -> bool:
        raise NotImplementedError("HTTPS git protocol not yet implemented")

    def configure_remote(self, repo_path: str, remote_url: str) -> None:
        raise NotImplementedError("HTTPS git protocol not yet implemented")
