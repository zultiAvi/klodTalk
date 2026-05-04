---
skill_name: extra-files-config
triggers:
  - Adding or documenting per-project config fields that copy host files into the session workspace
  - Working on `copy_git_tracked` or its callers in `session_manager.py`
  - User asks for gitignored files (`.env`, local configs) to be available inside session containers
summary: `extra_files` config copies gitignored host files (or dirs) into session workspaces after `git reset --hard`. Top-level for single-repo, per-repo for multi-repo; `..` and absolute paths rejected.
---

# Skill: extra_files Project Config

## Quick Reference
- Field name: `extra_files`. Lives in `config/projects.json` per project.
- Single-repo project (no `repos` key): top-level list of paths relative to `folder`.
- Multi-repo project (with `repos`): place inside each `repos[i]` entry, paths relative to that repo. Top-level is **ignored with a warning** when `repos` is present.
- Implemented in `server/copy_tree.py:copy_git_tracked(src, dst, extra_files=None)` and read by `server/session_manager.py:_extract_extra_files()`.
- Safety: absolute paths and `..` traversal are rejected with a warning. Missing entries are warnings (non-fatal). Both files and directories are supported.
- Documented in `config/CLAUDE.md` under the projects.json schema.

## When to Use
When the user asks to mirror host files into session workspaces (gitignored configs, `.env` files, local secrets, build artifacts), when reviewing changes to `copy_git_tracked` or its callers, or when adding a new project config field that touches workspace copy.

## Schema Examples

Single-repo:
```json
{
  "folder": "/home/me/proj",
  "extra_files": [".env", "config/local.json"]
}
```

Multi-repo:
```json
{
  "folder": "/home/me/proj",
  "repos": [
    {"path": "frontend", "extra_files": [".env.local"]},
    {"path": "backend",  "extra_files": [".env"]}
  ]
}
```

## Behavior Contract
- Files are copied AFTER `git reset --hard HEAD` reconstructs tracked content. If a tracked file and an extra share a path, the extra (host working-tree copy) overwrites the committed version.
- `progress.files_copied` and `progress.total_bytes` include extras (so progress reporting stays coherent).
- Failures are logged as warnings (`log.warning`). Never raise — workspace creation must keep going.

## When to Extend
- New safety guard? Add it to the `# 2c. Copy extra files` block in `copy_tree.py`. Add a corresponding test in `tests/test_copy_tree.py` (mirror the `test_copy_git_tracked_extra_files_*` family).
- New schema variant? Update `_extract_extra_files` in `session_manager.py` AND `config/CLAUDE.md`. Keep the helper's type guards permissive (warn-and-skip, not raise).
