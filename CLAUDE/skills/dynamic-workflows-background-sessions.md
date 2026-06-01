---
skill_name: dynamic-workflows-background-sessions
triggers:
  - A Coder or TestRunner role is about to run a long pytest/npm/cargo build that blocks the agent
  - You want to keep the foreground agent responsive (BTW side-channel) while a build runs
  - Pipeline step needs async dispatch + completion sentinel for the next role to gate on
summary: "`! <command>` (space after `!`) dispatches a shell command in a background session in Claude Code v2.1.154+; poll via `claude bg status <session-id>` or a sentinel file. Opt-in pending container version confirmation."
---

# Skill: Dynamic Workflows -- `! <command>` Background Sessions

## Quick Reference
- Syntax: `! <shell command>` (note the **space after the `!`**; without it, the line is treated as a regular shell prefix, not a background dispatch).
- Polling: `claude bg status <session-id>` for status; or write a sentinel file (e.g. `touch .klodTalk/team/current/build_done`) and have the next role gate on it.
- CLI requirement: Claude Code **v2.1.154+** (Dynamic Workflows release, May 28 2026).
- Container caveat: `Dockerfile.agent` is pinned (currently @2.90.0). Treat as **opt-in pending version confirmation** -- run `claude --version` inside the agent container before relying on it. Companion: `background-session-isolation.md`.

## When to Use
- **Coder role** running long compile steps (`cargo build`, `npm run build`, large Python test suites).
- **TestRunner role** running full `pytest -x` or integration suites that take minutes.
- Any pipeline step where the foreground agent could be drafting `out_message.txt` / `handoff.md` while the build crunches.

## Pattern

1. Dispatch the slow command in the background:
   ```
   ! pytest -x tests/ ; touch .klodTalk/team/current/build_done
   ```
2. Continue with foreground work (write handoff, plan next steps).
3. Before handoff, gate on the sentinel:
   ```bash
   while [ ! -f .klodTalk/team/current/build_done ]; do sleep 5; done
   ```
4. The downstream **Reviewer** reads the sentinel + the log spill (see `large-output-spill.md`) -- not the live process.

## Constraints
- The pinned `Dockerfile.agent` may not yet ship a CLI version that supports the `! <cmd>` syntax. Confirm with `claude --version` before adding `!`-prefixed dispatches to role files. Until confirmed, leave this as documented opt-in only.
- Background-session **isolation**: see `background-session-isolation.md` -- KlodTalk requires `worktree.bgIsolation: "none"` so background sessions write into the mounted `/workspace`.
- Do not commit sentinel files (`build_done`, etc.); they live under the gitignored `.klodTalk/` tree.

## Related
- `background-session-isolation.md` -- worktree.bgIsolation must be `"none"` for KlodTalk containers.
- `large-output-spill.md` -- spill long build logs to a sidecar file rather than into `out_message.txt`.
- `docker-claude-stability.md` -- Dockerfile.agent pinning policy.

## Source
- anthropics/claude-code v2.1.154 release notes (Dynamic Workflows / `! <command>` background sessions) -- https://github.com/anthropics/claude-code/releases
