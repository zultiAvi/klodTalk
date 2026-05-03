---
skill_name: git-submodule-init-after-clone
triggers:
  - Modifying `server/copy_tree.py` or any session-workspace copy logic
  - Reproducing a git repo from a copied `.git/` directory
  - Diagnosing empty submodule directories after a fresh checkout/copy
summary: After `git reset --hard HEAD`, submodules are NOT auto-initialized; run `git submodule update --init --recursive` separately.
---

# Skill: Initialize Submodules After Repo Reconstruction

## Quick Reference
- `git reset --hard HEAD` restores `.gitmodules` but leaves submodule paths as empty gitlinks.
- Run `git submodule update --init --recursive` after the reset to populate working trees.
- Gate on `(dst_path / ".gitmodules").is_file()` to keep non-submodule repos a no-op.
- Failure should be warning-only (`check=False`, log via `log.warning`), never abort the outer copy.

## When to Use
When writing or reviewing logic that reconstructs a git working tree from a copied `.git/` directory (e.g. `server/copy_tree.py:copy_git_tracked()`), or whenever a "session workspace looks empty" symptom points at submodules.

## Pattern

```python
# After: subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=str(dst_path), check=True)

if (dst_path / ".gitmodules").is_file():
    log.info("Initializing submodules in '%s'", dst)
    try:
        sub_result = subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=str(dst_path), capture_output=True, text=True, check=False,
        )
        if sub_result.returncode != 0:
            log.warning("git submodule update failed in '%s': %s",
                        dst, sub_result.stderr.strip())
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        log.warning("Failed to initialize submodules in '%s': %s", dst, exc)
```

## Counting submodule files

`git ls-files` on the outer repo only lists the gitlink path (e.g. `sub`), not the submodule's tracked files. To include them in a progress count:

```python
sub_files = subprocess.run(
    ["git", "submodule", "foreach", "--quiet", "--recursive",
     'git ls-files | sed "s|^|$displaypath/|"'],
    cwd=str(dst_path), capture_output=True, text=True, check=False,
)
```

`$displaypath` is git's per-submodule-relative path inside `foreach`. The shell expansion is platform-sensitive — if portability matters, parse `.gitmodules` and run `git ls-files` per submodule directory in Python instead.

## Testing pattern (file:// submodule)

```python
subprocess.run(
    ["git", "-c", "protocol.file.allow=always", "submodule", "add",
     f"file://{submodule_src}", "sub"],
    cwd=str(outer), check=True,
)
```

Wrap in `try/except subprocess.CalledProcessError` -> `pytest.skip(...)` because some sandboxed CI environments forbid `file://` submodules.

## Why warning-only

The outer-repo copy is independently useful even when submodule init fails (no network, bad URL, missing submodule remote). Aborting would regress the existing single-repo behavior.
