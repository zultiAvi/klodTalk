"""Tests for copy_tree module."""

import os
import subprocess
import sys

import pytest

# copy_tree lives one level up; make it importable without packaging.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from copy_tree import CopyProgress, copy_git_tracked, copy_tree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_file(path, content="data"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _read(path):
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBasicCopy:
    def test_copies_all_files_and_dirs(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "aaa")
        _make_file(src / "sub" / "b.txt", "bbb")

        copy_tree(str(src), str(dst))

        assert _read(dst / "a.txt") == "aaa"
        assert _read(dst / "sub" / "b.txt") == "bbb"

    def test_preserves_empty_dirs(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        (src / "empty_dir").mkdir(parents=True)
        _make_file(src / "keep.txt")

        copy_tree(str(src), str(dst))

        assert (dst / "empty_dir").is_dir()


class TestGitDirectory:
    def test_includes_git_dir_by_default(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".git" / "HEAD", "ref: refs/heads/main\n")
        _make_file(src / "file.txt")

        copy_tree(str(src), str(dst))

        assert (dst / ".git" / "HEAD").is_file()

    def test_excludes_git_dir_when_disabled(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".git" / "HEAD", "ref: refs/heads/main\n")
        _make_file(src / "file.txt")

        copy_tree(str(src), str(dst), include_git=False)

        assert not (dst / ".git").exists()
        assert (dst / "file.txt").is_file()


class TestFilterFilename:
    def test_no_filter_by_default(self, tmp_path):
        """Files matching typical gitignore patterns ARE copied when no filter is set."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".gitignore", "build/\n*.log\n")
        _make_file(src / "build" / "output.js", "built")
        _make_file(src / "error.log", "log line")
        _make_file(src / "main.py", "code")

        copy_tree(str(src), str(dst))

        assert (dst / "build" / "output.js").is_file()
        assert (dst / "error.log").is_file()
        assert (dst / "main.py").is_file()

    def test_gitignore_filter_when_enabled(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".gitignore", "*.log\nsecret.txt\n")
        _make_file(src / "error.log", "log")
        _make_file(src / "secret.txt", "shh")
        _make_file(src / "main.py", "code")

        copy_tree(str(src), str(dst), filter_filename=".gitignore")

        assert not (dst / "error.log").exists()
        assert not (dst / "secret.txt").exists()
        assert (dst / "main.py").is_file()

    def test_nested_gitignore(self, tmp_path):
        """Nested .gitignore files stack correctly with parent patterns."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".gitignore", "*.log\n")
        _make_file(src / "sub" / ".gitignore", "*.tmp\n")
        _make_file(src / "root.log", "log")
        _make_file(src / "sub" / "nested.log", "log")
        _make_file(src / "sub" / "data.tmp", "tmp")
        _make_file(src / "sub" / "keep.txt", "keep")
        _make_file(src / "root.tmp", "tmp at root")

        copy_tree(str(src), str(dst), filter_filename=".gitignore")

        # Parent pattern *.log applies everywhere
        assert not (dst / "root.log").exists()
        assert not (dst / "sub" / "nested.log").exists()
        # Nested pattern *.tmp only applies in sub/
        assert not (dst / "sub" / "data.tmp").exists()
        # *.tmp does NOT apply at root level
        assert (dst / "root.tmp").is_file()
        # Non-ignored file is kept
        assert (dst / "sub" / "keep.txt").is_file()

    def test_gitignore_directory_pattern(self, tmp_path):
        """Directory patterns (e.g. build/) match directories."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".gitignore", "build/\n")
        _make_file(src / "build" / "out.js", "built")
        _make_file(src / "main.py", "code")

        copy_tree(str(src), str(dst), filter_filename=".gitignore")

        assert not (dst / "build").exists()
        assert (dst / "main.py").is_file()

    def test_copies_gitignore_file_itself(self, tmp_path):
        """The .gitignore file itself is copied even when filtering is enabled."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".gitignore", "*.log\n")
        _make_file(src / "main.py", "code")

        copy_tree(str(src), str(dst), filter_filename=".gitignore")

        assert (dst / ".gitignore").is_file()
        assert _read(dst / ".gitignore") == "*.log\n"


class TestCopyProgress:
    def test_copy_tree_returns_progress(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "aaa")
        _make_file(src / "sub" / "b.txt", "bb")

        progress = copy_tree(str(src), str(dst))

        assert progress.files_copied == 2
        assert progress.total_bytes == 5

    def test_copy_tree_progress_excludes_filtered(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / ".gitignore", "*.log\n")
        _make_file(src / "keep.txt", "data")
        _make_file(src / "skip.log", "logdata")

        progress = copy_tree(str(src), str(dst), filter_filename=".gitignore")

        # .gitignore + keep.txt copied, skip.log filtered out
        assert progress.files_copied == 2
        assert progress.total_bytes == len("*.log\n") + len("data")

    def test_copy_git_tracked_returns_progress(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "tracked.txt", "hello")
        _make_file(src / "untracked.txt", "skip")
        _git(src, "add", "tracked.txt")
        _git(src, "commit", "-m", "init")

        progress = copy_git_tracked(str(src), str(dst))

        assert progress.files_copied == 1
        assert progress.total_bytes == 5

    def test_progress_properties(self):
        p = CopyProgress()
        p.files_copied = 3
        p.total_bytes = 2048
        assert p.total_kb == 2.0
        assert p.total_mb == 2048 / (1024 * 1024)


class TestSymlinks:
    def test_skips_symlinks(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "real.txt", "data")
        (src / "link.txt").symlink_to(src / "real.txt")
        (src / "dir_link").symlink_to(src)

        copy_tree(str(src), str(dst))

        assert (dst / "real.txt").is_file()
        assert not (dst / "link.txt").exists()
        assert not (dst / "dir_link").exists()


class TestMergeAndErrors:
    def test_merges_existing_dst(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "new.txt", "new")
        _make_file(dst / "existing.txt", "existing")

        copy_tree(str(src), str(dst))

        assert _read(dst / "new.txt") == "new"
        assert _read(dst / "existing.txt") == "existing"

    def test_raises_on_invalid_src(self, tmp_path):
        with pytest.raises(ValueError, match="not a directory"):
            copy_tree(str(tmp_path / "nonexistent"), str(tmp_path / "dst"))

    def test_raises_on_file_as_src(self, tmp_path):
        src_file = tmp_path / "file.txt"
        src_file.write_text("not a dir")
        with pytest.raises(ValueError, match="not a directory"):
            copy_tree(str(src_file), str(tmp_path / "dst"))


# ---------------------------------------------------------------------------
# Helpers for git-based tests
# ---------------------------------------------------------------------------

def _git(repo_path, *args):
    """Run a git command in the given repo directory."""
    subprocess.run(
        ["git", *args],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )


def _init_git_repo(path):
    """Create a git repo with an initial commit."""
    os.makedirs(path, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.name", "Test")
    _git(path, "config", "user.email", "test@test.com")


# ---------------------------------------------------------------------------
# Tests for copy_git_tracked
# ---------------------------------------------------------------------------

class TestCopyGitTracked:
    def test_copies_only_committed_files(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "tracked.txt", "yes")
        _make_file(src / "untracked.txt", "no")
        _git(src, "add", "tracked.txt")
        _git(src, "commit", "-m", "init")

        copy_git_tracked(str(src), str(dst))

        assert _read(dst / "tracked.txt") == "yes"
        assert not (dst / "untracked.txt").exists()

    def test_restores_committed_state_not_working_tree(self, tmp_path):
        """Uncommitted modifications are NOT copied — committed content is restored."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "file.txt", "committed")
        _git(src, "add", "file.txt")
        _git(src, "commit", "-m", "init")
        # Modify without committing
        _make_file(src / "file.txt", "dirty")

        copy_git_tracked(str(src), str(dst))

        assert _read(dst / "file.txt") == "committed"

    def test_copies_git_directory(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "file.txt", "data")
        _git(src, "add", "file.txt")
        _git(src, "commit", "-m", "init")

        copy_git_tracked(str(src), str(dst))

        assert (dst / ".git").is_dir()
        assert (dst / ".git" / "HEAD").is_file()

    def test_handles_symlinked_tracked_files(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "real.txt", "symlinked content")
        os.symlink(str(src / "real.txt"), str(src / "link.txt"))
        _git(src, "add", "real.txt", "link.txt")
        _git(src, "commit", "-m", "init")

        copy_git_tracked(str(src), str(dst))

        # git reset --hard restores the symlink target content
        assert (dst / "link.txt").exists()
        assert _read(dst / "link.txt") == "symlinked content"

    def test_fallback_when_not_git_repo(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "aaa")
        _make_file(src / "b.txt", "bbb")

        copy_git_tracked(str(src), str(dst))

        # Falls back to copy_tree — both files copied
        assert _read(dst / "a.txt") == "aaa"
        assert _read(dst / "b.txt") == "bbb"

    def test_preserves_directory_structure(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "a" / "b" / "c.txt", "deep")
        _make_file(src / "top.txt", "top")
        _git(src, "add", ".")
        _git(src, "commit", "-m", "init")

        copy_git_tracked(str(src), str(dst))

        assert _read(dst / "a" / "b" / "c.txt") == "deep"
        assert _read(dst / "top.txt") == "top"

    def test_preserves_executable_permission(self, tmp_path):
        """Git stores executable bit — verify it's restored."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _init_git_repo(src)
        _make_file(src / "script.sh", "#!/bin/sh\necho hi")
        os.chmod(src / "script.sh", 0o755)
        _git(src, "add", "script.sh")
        _git(src, "commit", "-m", "init")

        copy_git_tracked(str(src), str(dst))

        assert os.access(dst / "script.sh", os.X_OK)
