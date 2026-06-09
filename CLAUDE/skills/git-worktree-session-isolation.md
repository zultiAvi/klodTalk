---
skill_name: git-worktree-session-isolation
triggers:
  - Two sessions need to work the same project repo concurrently without colliding
  - Designing per-session branch/checkout isolation for the KlodTalk session lifecycle
  - Using the git worktree helpers in server/utils/git_utils.sh / git_utils.py
summary: "Per-session git worktree helpers: each session gets its own checkout at /workspace/.worktrees/<session_id> on branch session/<session_id>, so concurrent same-project sessions don't step on each other; cleanup on session delete."
---

# Skill: Git Worktree Session Isolation

## When to Use
- Multiple users/sessions run against the **same** project repo at once. KlodTalk isolates agents by Docker container but they share one mounted `/workspace` checkout, so two sessions on the same project can collide (each merges `base_branch` before working).
- You want each session to have its own branch + working tree instead of a single shared checkout.
- Not needed for single-session-per-project workflows.

## Helpers
Shell (`server/utils/git_utils.sh`):
- `git_create_session_worktree <session_id> <base_branch>` — creates the worktree, prints its path.
- `git_remove_session_worktree <session_id>` — force-removes it and prunes.

Python mirror (`server/utils/git_utils.py`):
- `create_session_worktree(session_id, base_branch, cwd=...)` → path
- `remove_session_worktree(session_id, cwd=...)`

## Conventions
- **Path**: `/workspace/.worktrees/<session_id>`
- **Branch**: `session/<session_id>`, created from `origin/<base_branch>`
- **Idempotent**: an existing path/branch is reused, not re-created (re-attach an existing worktree branch).
- **Cleanup**: call the remove helper when a session is deleted/closed; it uses `git worktree remove --force` (so dirty trees are still removed) then `git worktree prune`.

## IMPORTANT — Manual Follow-up (out of scope here)
Wiring these helpers into the session lifecycle lives in `server/session_manager.py` (and `server/server.py`), which are **core code** and were NOT edited by this change. The integration is a **separate, manual step**: call `create_session_worktree` at session start and `remove_session_worktree` on `delete_session`, and point the agent's `cwd` at the returned worktree path. Until that wiring lands, these are reusable utilities only.

## Source
ComposioHQ/agent-orchestrator — https://github.com/ComposioHQ/agent-orchestrator (~7.5k stars): each agent works in its own git worktree + branch rather than a shared checkout.
