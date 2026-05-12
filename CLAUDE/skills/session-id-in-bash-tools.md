---
skill_name: session-id-in-bash-tools
triggers:
  - Writing Bash-tool scripts that need a session identity
  - Debugging interleaved log output from parallel KlodTalk sessions
  - Tagging temp files or per-session log paths from helper shell scripts
summary: `CLAUDE_CODE_SESSION_ID` is available in Bash-tool subprocesses since Claude Code v2.1.132; use it for log tagging and temp-file isolation.
---

# Skill: Session ID in Bash-Tool Scripts

## Quick Reference
- Env var: `CLAUDE_CODE_SESSION_ID` (Claude Code v2.1.132+)
- Scope: Bash tool subprocesses only — **NOT** in hook scripts (different env)
- Pattern: `SESSION_ID="${CLAUDE_CODE_SESSION_ID:-unknown}"`
- Companion: `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1` for Docker TTY stability

## When to Use
- Writing a new helper script under `server/utils/*.sh` that needs per-session log attribution.
- Debugging cases where multiple sessions interleave output in shared log files.
- Creating temp files that must not collide across parallel agent containers.

## Instructions

### Pattern
```bash
SESSION_ID="${CLAUDE_CODE_SESSION_ID:-unknown}"
LOG_FILE="/tmp/klodTalk_${SESSION_ID}.log"
echo "[$(date -u +%FT%TZ)] [${SESSION_ID}] starting" >> "${LOG_FILE}"
```

### Scope Note
- The variable is set by Claude Code only when the script is invoked via the **Bash tool**.
- It is **not** present in hook scripts (`PostToolUse`, `PostToolUseFailure`, etc.) — hook env is a separate context. For effort tagging in hooks, see `hook-event-logging` skill and `$CLAUDE_EFFORT`.
- Always default with `${CLAUDE_CODE_SESSION_ID:-unknown}` so the script keeps working on older CLI pins or outside Claude.

### Companion Variable
- `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1` suppresses fullscreen terminal rendering — useful inside agent Docker containers where the alternate screen buffer corrupts logged stdout. Set at container env level (`docker exec -e ...`) or via session-launch env, **not** in `Dockerfile.agent` (restricted).

### See Also
- `session-data-path-propagation` — path-routing patterns for per-session output.
- `hook-event-logging` — hook env has `$CLAUDE_EFFORT` but not `$CLAUDE_CODE_SESSION_ID`.

### Source
Claude Code v2.1.132 release: https://github.com/anthropics/claude-code/releases/tag/v2.1.132 (github.com/anthropics/claude-code, 82,000+ stars).
