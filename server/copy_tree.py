"""Gitignore-aware directory copy, replacing shutil.copytree."""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pathspec

log = logging.getLogger(__name__)

# Log progress every N files when total is unknown, or every P% when known.
_PROGRESS_EVERY_N = 50
_PROGRESS_EVERY_PCT = 10


class CopyProgress:
    """Tracks and logs progress during a copy operation."""

    def __init__(self, total: Optional[int] = None) -> None:
        self.files_copied: int = 0
        self.total_bytes: int = 0
        self._total: Optional[int] = total
        self._next_log_at: int = _PROGRESS_EVERY_N  # count-based threshold
        self._next_pct: int = _PROGRESS_EVERY_PCT   # percentage threshold

    def record(self, size: int) -> None:
        """Record one copied file and log progress at intervals."""
        self.files_copied += 1
        self.total_bytes += size

        if self._total is not None:
            pct = (self.files_copied * 100) // self._total
            if pct >= self._next_pct:
                log.info("Copying workspace: %d/%d files (%d%%)",
                         self.files_copied, self._total, pct)
                self._next_pct = pct + _PROGRESS_EVERY_PCT
        else:
            if self.files_copied >= self._next_log_at:
                log.info("Copying workspace: %d files copied...",
                         self.files_copied)
                self._next_log_at += _PROGRESS_EVERY_N

    def done(self) -> None:
        """Log a final summary line."""
        if self.total_mb >= 1:
            size_str = f"{self.total_mb:.1f} MB"
        elif self.total_kb >= 1:
            size_str = f"{self.total_kb:.1f} KB"
        else:
            size_str = f"{self.total_bytes} B"
        log.info("Copy complete: %d files, %s", self.files_copied, size_str)

    @property
    def total_kb(self) -> float:
        return self.total_bytes / 1024

    @property
    def total_mb(self) -> float:
        return self.total_bytes / (1024 * 1024)


def copy_tree(
    src: str,
    dst: str,
    filter_filename: Optional[str] = None,
    include_git: bool = True,
) -> CopyProgress:
    """Copy directory tree from src to dst, skipping symlinks and filtered files.

    Args:
        src: Source directory path.
        dst: Destination directory path (created if needed; merged if exists).
        filter_filename: Name of gitignore-style filter file to look for in each
            directory (e.g. ".gitignore"). Set to None (default) to disable filtering.
        include_git: If True (default), the ".git" directory is included.
            Set to False to exclude it.

    Returns:
        CopyProgress with the number of files copied and total bytes.
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.is_dir():
        raise ValueError(f"Source is not a directory: {src}")

    progress = CopyProgress()
    _copy_tree_recursive(src_path, dst_path, filter_filename, parent_specs=[], include_git=include_git, progress=progress)
    progress.done()
    return progress


def _load_filter_spec(directory: Path, filter_filename: str) -> Optional[pathspec.PathSpec]:
    """Load a gitignore-style filter spec from a directory, if the file exists."""
    filter_file = directory / filter_filename
    if filter_file.is_file():
        try:
            patterns = filter_file.read_text(encoding="utf-8", errors="replace").splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except Exception:
            return None
    return None


def _is_ignored(rel_path: str, is_dir: bool, specs: list[pathspec.PathSpec]) -> bool:
    """Check if a relative path is matched by any of the stacked filter specs."""
    check_path = rel_path + "/" if is_dir else rel_path
    for spec in specs:
        if spec.match_file(check_path):
            return True
    return False


def _copy_tree_recursive(
    src: Path,
    dst: Path,
    filter_filename: Optional[str],
    parent_specs: list[pathspec.PathSpec],
    include_git: bool = False,
    progress: Optional[CopyProgress] = None,
) -> None:
    """Recursively copy src to dst, applying stacked gitignore filters."""
    dst.mkdir(parents=True, exist_ok=True)

    # Load filter spec for this directory level and stack it
    specs = list(parent_specs)
    if filter_filename:
        local_spec = _load_filter_spec(src, filter_filename)
        if local_spec:
            specs.append(local_spec)

    for entry in os.scandir(src):
        # Always skip symlinks
        if entry.is_symlink():
            continue

        # Skip .git directories unless explicitly included
        if entry.name == ".git" and entry.is_dir(follow_symlinks=False) and not include_git:
            continue

        # Check against stacked filter specs
        if filter_filename and specs and _is_ignored(entry.name, entry.is_dir(follow_symlinks=False), specs):
            continue

        src_entry = Path(entry.path)
        dst_entry = dst / entry.name

        if entry.is_dir(follow_symlinks=False):
            _copy_tree_recursive(src_entry, dst_entry, filter_filename, specs, include_git=include_git, progress=progress)
        elif entry.is_file(follow_symlinks=False):
            shutil.copy2(entry.path, dst_entry)
            if progress is not None:
                progress.record(entry.stat(follow_symlinks=False).st_size)


def copy_git_tracked(
    src: str,
    dst: str,
    extra_files: Optional[list[str]] = None,
) -> CopyProgress:
    """Copy a git repo by copying ``.git/`` and reconstructing the working tree.

    Copies only the ``.git`` directory from *src* to *dst*, then runs
    ``git reset --hard HEAD`` in the destination to reconstruct all tracked
    files with correct content, permissions, and symlinks.

    Falls back to ``copy_tree(src, dst)`` if *src* is not a git repository.

    Args:
        src: Source repository path.
        dst: Destination path.
        extra_files: Optional list of paths (relative to *src*) to copy
            verbatim from the original folder after the working tree is
            reconstructed. Useful for gitignored files that the user wants
            present in the session (e.g. ``.env``, local config). Missing
            entries are skipped with a warning. Absolute paths and ``..``
            traversal are rejected.

    Returns:
        CopyProgress with the number of files restored and total bytes.
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.is_dir():
        raise ValueError(f"Source is not a directory: {src}")

    src_git = src_path / ".git"
    if not src_git.is_dir():
        log.warning("No .git in '%s', falling back to copy_tree", src)
        return copy_tree(src, dst)

    dst_path.mkdir(parents=True, exist_ok=True)

    # 1. Copy only the .git directory
    dst_git = dst_path / ".git"
    log.info("Copying .git directory from '%s'", src)
    shutil.copytree(str(src_git), str(dst_git), symlinks=False, dirs_exist_ok=True)

    # 2. Reconstruct working tree from git objects
    log.info("Reconstructing working tree via git reset --hard")
    try:
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            cwd=str(dst_path),
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        log.warning("git reset --hard failed in '%s' (%s), falling back to copy_tree", dst, exc)
        # Clean up partial .git copy before fallback
        shutil.rmtree(str(dst_git), ignore_errors=True)
        return copy_tree(src, dst)

    # DISABLED 2026-05-04: submodules are intentionally NOT initialized during session
    # copy (per user request -- submodules in repos cause friction). Block kept commented
    # so it can be re-enabled by uncommenting if requirements change.
    # # 2b. Initialize submodules (if any) so working trees are populated.
    # if (dst_path / ".gitmodules").is_file():
    #     log.info("Initializing submodules in '%s'", dst)
    #     try:
    #         sub_result = subprocess.run(
    #             ["git", "submodule", "update", "--init", "--recursive"],
    #             cwd=str(dst_path),
    #             capture_output=True,
    #             text=True,
    #             check=False,
    #         )
    #         if sub_result.returncode != 0:
    #             log.warning(
    #                 "git submodule update --init --recursive failed in '%s': %s",
    #                 dst, sub_result.stderr.strip(),
    #             )
    #     except (FileNotFoundError, subprocess.SubprocessError) as exc:
    #         log.warning("Failed to initialize submodules in '%s': %s", dst, exc)

    # 2c. Copy extra (often gitignored) files from src that the user wants in the session.
    extra_count = 0
    extra_bytes = 0
    if extra_files:
        for rel in extra_files:
            if not isinstance(rel, str) or not rel:
                log.warning("Skipping invalid extra_files entry: %r", rel)
                continue
            if os.path.isabs(rel) or ".." in Path(rel).parts:
                log.warning("Skipping unsafe extra_files entry: %s", rel)
                continue
            src_file = src_path / rel
            dst_file = dst_path / rel
            try:
                if src_file.is_file():
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src_file), str(dst_file))
                    size = src_file.stat().st_size
                    extra_count += 1
                    extra_bytes += size
                    log.info("Copied extra file '%s' (%d bytes)", rel, size)
                elif src_file.is_dir():
                    shutil.copytree(str(src_file), str(dst_file), dirs_exist_ok=True)
                    for sub in src_file.rglob("*"):
                        if sub.is_file():
                            extra_count += 1
                            extra_bytes += sub.stat().st_size
                    log.info("Copied extra dir '%s'", rel)
                else:
                    log.warning("extra_files entry not found, skipping: %s", src_file)
            except Exception as exc:
                log.warning("Failed to copy extra '%s': %s", rel, exc)

    # 3. Count restored files for progress reporting (outer + submodules)
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=str(dst_path),
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [f for f in result.stdout.splitlines() if f]

    # DISABLED 2026-05-04: submodule file enumeration removed alongside submodule init
    # (see 2b). With submodules no longer checked out, `git submodule foreach` would
    # either no-op or error.
    # # Append submodule files when present.
    # if (dst_path / ".gitmodules").is_file():
    #     try:
    #         sub_files = subprocess.run(
    #             ["git", "submodule", "foreach", "--quiet", "--recursive",
    #              "git ls-files | sed \"s|^|$displaypath/|\""],
    #             cwd=str(dst_path),
    #             capture_output=True,
    #             text=True,
    #             check=False,
    #         )
    #         if sub_files.returncode == 0:
    #             tracked.extend(f for f in sub_files.stdout.splitlines() if f)
    #     except (FileNotFoundError, subprocess.SubprocessError) as exc:
    #         log.warning("Failed to enumerate submodule files in '%s': %s", dst, exc)

    total_bytes = sum(
        (dst_path / f).stat().st_size
        for f in tracked
        if (dst_path / f).is_file()
    )

    progress = CopyProgress(total=len(tracked))
    progress.files_copied = len(tracked) + extra_count
    progress.total_bytes = total_bytes + extra_bytes
    progress.done()
    return progress

