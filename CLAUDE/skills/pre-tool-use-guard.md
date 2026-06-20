---
skill_name: pre-tool-use-guard
triggers:
  - Adding defence-in-depth against destructive Bash commands in agent containers
  - Registering a PreToolUse hook that blocks rm -rf, git reset --hard, etc.
  - Hardening a Coder or Executor role that runs against a bind-mounted workspace
summary: "Use server/utils/hooks/pre_tool_use_guard.sh as a PreToolUse hook (matcher Bash, continueOnBlock true) to refuse destructive commands before they hit the host-mounted /workspace."
---

# Skill: PreToolUse Destructive-Command Guard

## Instructions

KlodTalk agents run inside Docker containers with `/workspace` bind-mounted from the host. The container boundary does not protect the mounted volume -- `rm -rf /workspace` from inside the agent still destroys host files. This hook is the defence-in-depth layer at the tool-call level.

**Script:** `server/utils/hooks/pre_tool_use_guard.sh` (executable; exits 0 on allow, 2 on block).

**Deny-list (narrow -- extend deliberately):**
- `rm -rf` / `rm -fr` (any flag order containing both r and f)
- `git reset --hard`
- `git push` — ALL plain pushes are now blocked, not just `--force`/`-f`. KlodTalk agents never push (the server pushes after the agent finishes); Web/Android task-agent sub-agents may auto-push despite CLAUDE.md (issue #56865), so the hook is the only defence. See `task-agent-auto-push-guard.md`. The `--force`/`-f` patterns remain (subsumed but explicit).
- `chmod 777`, `dd ... of=/dev/...`, `mkfs`
- `shutdown` / `reboot` (anchored to command position)

**Register in `.claude/settings.json`** (not modified by this skill -- register at container build / operator deployment time):
```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","continueOnBlock":true,
  "hooks":[{"type":"command",
    "command":"bash /workspace/server/utils/hooks/pre_tool_use_guard.sh"}]}]}}
```

**Critical caveat (per instincts.md line 7):** role YAML frontmatter forwards ONLY `mcpServers` and `disallowedTools`. A `hooks:` key in role frontmatter is silently ignored. Hook registration MUST happen at the container level via `.claude/settings.json`.

**Behaviour:**
- Reads stdin JSON (`tool_name`, `tool_input.command`); uses `jq` with a raw `grep`/`sed` fallback. Only inspects `tool_name == Bash`.
- On match: writes `Refused: destructive command pattern '<pattern>' matched` to stderr and exits 2. Claude receives the stderr as feedback via continueOnBlock and can adjust.
- On no match: exits 0.

**Extending the deny-list:** keep it narrow. False positives that block legitimate commands are worse than the hook not existing. Prefer word-boundary or argument-bounded regex (`\b`, `[[:space:]]`) over loose substrings, and anchor against `--<longopt>` collisions (see `--force` vs `--force-with-lease`).

## Source
disler/claude-code-hooks-mastery -- https://github.com/disler/claude-code-hooks-mastery (~3,700 stars).
