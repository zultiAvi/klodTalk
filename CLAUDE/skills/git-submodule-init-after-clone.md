---
skill_name: git-submodule-init-after-clone
triggers:
  - Modifying `server/copy_tree.py` or any session-workspace copy logic
  - Considering whether to (re-)enable submodule initialization in `copy_git_tracked`
  - Diagnosing empty submodule directories after a fresh checkout/copy
summary: Submodule init in `copy_git_tracked` is INTENTIONALLY DISABLED (2026-05-04). Do not re-enable without owner sign-off; use `extra_files` for gitignored content.
---

# Skill: Submodule Init in copy_git_tracked is Disabled

## Quick Reference
- As of 2026-05-04, `copy_git_tracked` does NOT run `git submodule update --init --recursive`. Both the init block and the `git submodule foreach` enumeration block are commented out under `# DISABLED 2026-05-04:` markers in `server/copy_tree.py`.
- Decision is owner-driven: submodules in repos cause friction during session creation. Empty submodule directories are an accepted side effect.
- For gitignored files (e.g. `.env`, local configs) that the user wants in every session, use the `extra_files` config — see `extra-files-config.md`.
- Test `tests/test_copy_tree.py:test_does_not_init_submodules` positively asserts the disabled behavior. Inverting it without an explicit user request is a regression.

## When to Use
When working on `copy_git_tracked` or surrounding session-copy logic, when reviewing PRs that touch the submodule blocks, or when a future request asks "why are submodules empty in my session" — the answer is intentional.

## How to Re-Enable (if a future request asks)

Both blocks are preserved as comments in `server/copy_tree.py`. To re-enable, uncomment them and remove the `# DISABLED 2026-05-04:` headers. Then update `test_does_not_init_submodules` accordingly. Confirm with the project owner first — disabling was an explicit decision.

## Original Pattern (kept for reference)

```python
# 2b. Initialize submodules (if any) so working trees are populated.
if (dst_path / ".gitmodules").is_file():
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

## Counting submodule files (if re-enabled)

`git ls-files` on the outer repo only lists the gitlink path. Use `git submodule foreach --quiet --recursive 'git ls-files | sed "s|^|$displaypath/|"'` to enumerate submodule files. `$displaypath` is shell-expanded inside `foreach`; if portability matters, parse `.gitmodules` and run `git ls-files` per submodule directory in Python instead.
