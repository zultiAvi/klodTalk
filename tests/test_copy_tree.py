"""Tests for copy_tree module."""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from copy_tree import CopyProgress, copy_tree, copy_git_tracked


def _make_file(path, content="data"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _read(path):
    with open(path) as f:
        return f.read()


class TestCopyProgress:
    def test_initial_state(self):
        p = CopyProgress()
        assert p.files_copied == 0
        assert p.total_bytes == 0

    def test_record_updates_counts(self):
        p = CopyProgress()
        p.record(100)
        assert p.files_copied == 1
        assert p.total_bytes == 100
        p.record(200)
        assert p.files_copied == 2
        assert p.total_bytes == 300

    def test_total_kb(self):
        p = CopyProgress()
        p.record(1024)
        assert p.total_kb == 1.0

    def test_total_mb(self):
        p = CopyProgress()
        p.record(1024 * 1024)
        assert p.total_mb == 1.0

    def test_with_total(self):
        p = CopyProgress(total=10)
        p.record(100)
        assert p.files_copied == 1

    def test_done_no_crash(self):
        p = CopyProgress()
        p.record(100)
        p.done()  # Should not raise

    def test_done_with_zero_bytes(self):
        p = CopyProgress()
        p.done()  # Should handle zero bytes

    def test_done_with_kb_range(self):
        p = CopyProgress()
        p.record(2048)
        p.done()  # Should show KB

    def test_done_with_mb_range(self):
        p = CopyProgress()
        p.record(2 * 1024 * 1024)
        p.done()  # Should show MB


class TestCopyTree:
    def test_copies_files(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "aaa")
        _make_file(src / "sub" / "b.txt", "bbb")

        copy_tree(str(src), str(dst))

        assert _read(dst / "a.txt") == "aaa"
        assert _read(dst / "sub" / "b.txt") == "bbb"

    def test_returns_progress(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "aaa")

        progress = copy_tree(str(src), str(dst))

        assert isinstance(progress, CopyProgress)
        assert progress.files_copied == 1
        assert progress.total_bytes == 3

    def test_empty_directory(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()

        progress = copy_tree(str(src), str(dst))
        assert progress.files_copied == 0
        assert progress.total_bytes == 0
        assert dst.is_dir()

    def test_nonexistent_source_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not a directory"):
            copy_tree(str(tmp_path / "nonexistent"), str(tmp_path / "dst"))

    def test_skips_symlinks(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "real.txt", "real")
        os.symlink(str(src / "real.txt"), str(src / "link.txt"))

        progress = copy_tree(str(src), str(dst))
        assert progress.files_copied == 1
        assert (dst / "real.txt").is_file()
        assert not (dst / "link.txt").exists()

    def test_exclude_git_dir(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "data")
        _make_file(src / ".git" / "config", "git config")

        copy_tree(str(src), str(dst), include_git=False)
        assert (dst / "a.txt").is_file()
        assert not (dst / ".git").exists()

    def test_include_git_dir(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "data")
        _make_file(src / ".git" / "config", "git config")

        copy_tree(str(src), str(dst), include_git=True)
        assert (dst / "a.txt").is_file()
        assert (dst / ".git" / "config").is_file()

    def test_deeply_nested(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a" / "b" / "c" / "d" / "deep.txt", "deep")

        copy_tree(str(src), str(dst))
        assert _read(dst / "a" / "b" / "c" / "d" / "deep.txt") == "deep"

    def test_filter_filename(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "keep.txt", "keep")
        _make_file(src / "skip.log", "skip")
        # Create a gitignore-style filter
        _make_file(src / ".gitignore", "*.log\n")

        progress = copy_tree(str(src), str(dst), filter_filename=".gitignore")
        assert (dst / "keep.txt").is_file()
        assert not (dst / "skip.log").exists()

    def test_many_files(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        for i in range(100):
            _make_file(src / f"file_{i}.txt", f"content_{i}")

        progress = copy_tree(str(src), str(dst))
        assert progress.files_copied == 100

    def test_preserves_file_content_exactly(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        content = "line1\nline2\ttab\n"
        _make_file(src / "special.txt", content)

        copy_tree(str(src), str(dst))
        assert _read(dst / "special.txt") == content


class TestCopyGitTracked:
    def test_copies_tracked_files(self, git_repo, tmp_path):
        dst = tmp_path / "dst"
        progress = copy_git_tracked(str(git_repo), str(dst))

        assert (dst / "tracked.txt").is_file()
        assert _read(dst / "tracked.txt") == "tracked content"
        assert progress.files_copied == 1

    def test_skips_untracked_files(self, git_repo, tmp_path):
        # Add an untracked file
        (git_repo / "untracked.txt").write_text("not tracked")

        dst = tmp_path / "dst"
        copy_git_tracked(str(git_repo), str(dst))

        assert (dst / "tracked.txt").is_file()
        assert not (dst / "untracked.txt").exists()

    def test_copies_git_dir(self, git_repo, tmp_path):
        dst = tmp_path / "dst"
        copy_git_tracked(str(git_repo), str(dst))

        assert (dst / ".git").is_dir()

    def test_nonexistent_source_raises(self, tmp_path):
        with pytest.raises(ValueError, match="not a directory"):
            copy_git_tracked(str(tmp_path / "nonexistent"), str(tmp_path / "dst"))

    def test_non_git_repo_falls_back(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        _make_file(src / "a.txt", "data")

        # Not a git repo, so should fall back to copy_tree
        progress = copy_git_tracked(str(src), str(dst))
        assert (dst / "a.txt").is_file()

    def test_handles_nested_tracked_files(self, git_repo, tmp_path):
        # Add a nested tracked file
        nested = git_repo / "sub" / "nested.txt"
        nested.parent.mkdir()
        nested.write_text("nested content")
        subprocess.run(["git", "add", "sub/nested.txt"], cwd=str(git_repo), capture_output=True)
        subprocess.run(["git", "commit", "-m", "add nested"], cwd=str(git_repo), capture_output=True)

        dst = tmp_path / "dst"
        progress = copy_git_tracked(str(git_repo), str(dst))

        assert (dst / "sub" / "nested.txt").is_file()
        assert _read(dst / "sub" / "nested.txt") == "nested content"
        assert progress.files_copied == 2  # tracked.txt + sub/nested.txt
