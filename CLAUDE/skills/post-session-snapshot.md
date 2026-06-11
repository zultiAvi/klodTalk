---
skill_name: post-session-snapshot
triggers:
  - Archiving each role's session transcript + token usage after a pipeline run
  - Debugging a pipeline failure where the role's container has already torn down
  - Wanting a per-role audit trail alongside coder_output.txt / reviewer_output.txt
summary: "PostSession lifecycle hook snapshots each role's session transcript + a token-usage summary into .klodTalk/team/current/ after the CLI session closes, surviving container teardown."
---

# Skill: PostSession Per-Role Output Snapshot

## Quick Reference
- Hook script: `server/utils/hooks/post_session_snapshot.sh`
- Registration: `.claude/settings.json` under `hooks.PostSession` with `"matcher": ""`.
- Fires at the **session** level (after the CLI session closes) — NOT the Task-tool
  sub-agent level (`subagent-lifecycle-hooks.md` covers that).
- Requires Claude Code **>= 2.1.169** (PostSession introduced there). Older CLIs
  never fire it — a silent no-op, not an error.
- Always `exit 0` (observational only; must not block session teardown).

## Output Files (in `.klodTalk/team/current/`)
- `post_session_log.jsonl` — one line per session:
  `{timestamp, event_type:"PostSession", session_id, role, input_tokens, output_tokens, cache_read_tokens}`.
- `session_transcript_<role>_<id8>.jsonl` — a copy of the session transcript, if
  the source can be located under `~/.claude/projects/<dashed-cwd>/sessions/`.

## Env Vars (all OPTIONAL — every access is guarded)
- `CLAUDE_CODE_SESSION_ID` — session id (falls back to the stdin JSON `.session_id`).
- `CLAUDE_CODE_ROLE` / `KLODTALK_ROLE` — role tag; defaults to `unknown`.
- `CLAUDE_CODE_USAGE_INPUT_TOKENS` / `_OUTPUT_TOKENS` / `_CACHE_READ_TOKENS` —
  token counts; fall back to the stdin JSON `.usage.*` fields, then `0`.

The exact PostSession env-var / stdin-payload names are a best-guess against the
2.1.169 changelog; the script is **defensive** — it tries env vars, then the
stdin envelope, then safe defaults, and always exits 0 even if every source is
absent. Adjust the field names here if a real run shows different keys.

## How the Orchestrator Uses It
Step 4 (run record / audit) can read `post_session_log.jsonl` for a per-role
token tally and open `session_transcript_<role>_*.jsonl` to inspect exactly what
a role did — without re-launching its (now-destroyed) container.

## Known Reliability Risks

PostSession/SessionEnd hooks are not guaranteed to complete on abrupt teardown
(anthropics/claude-code issue tracker):

- **Issue #41577** — SessionEnd/PostSession hooks may be **killed before async
  I/O completes** when the session ends abruptly (Ctrl+C, container teardown,
  Docker stop signal). **Issue #32712** — hooks are cancelled on Ctrl+C.
- **Defensive rule:** `post_session_snapshot.sh` must write all output files
  **synchronously** — no backgrounded subprocesses (`&`), no network / `curl`
  calls before the writes; complete every file write before the process exits.
  The script already exits 0, but write *ordering* is what lets the snapshot
  survive an abrupt kill: do the writes first, defer anything optional.
- **Fallback:** if the PostSession hook silently fails on abrupt teardown, the
  **PreCompact** hook (`precompact-context-guard.md`) fires more reliably for
  long-running sessions — consider writing a minimal fallback snapshot there too.
- **`/wrap-up` pattern** (inspired by issue #59273's `/exit`-writes-memory idea):
  a slash command agents invoke before an intentional exit to trigger the
  snapshot manually, bypassing the unreliable auto-hook timing window.

## Cross-References
- `subagent-lifecycle-hooks.md` — Task-tool sub-agent (SubagentStart/Stop) level.
- `multi-agent-hook-observability.md` — the shared JSONL observability pattern.
- `required-minimum-version-pin.md` — the 2.1.169/2.1.170 version floor.
- `precompact-context-guard.md` — reliability fallback: fires on PreCompact for
  long-running sessions when PostSession may be killed on abrupt teardown.

## Source
- anthropics/claude-code CHANGELOG v2.1.169 —
  https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
