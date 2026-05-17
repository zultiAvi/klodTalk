---
skill_name: pre-tool-use-guard
triggers:
  - Adding defence-in-depth against destructive Bash commands in agent containers
  - Registering a PreToolUse hook that blocks `rm -rf`, `git reset --hard`, etc.
  - Hardening a Coder or Executor role that runs against a bind-mounted workspace
summary: Use `server/utils/hooks/pre_tool_use_guard.sh` as a PreToolUse hook (matcher "Bash", `continueOnBlock: true`) to refuse destructive commands before they hit the host-mounted /workspace.
---

# Skill: PreToolUse Destructive-Command Guard

## Quick Reference
- Script: `server/utils/hooks/pre_tool_use_guard.sh` (executable, exits 0 on allow / 2 on block).
- Deny-list (narrow, starts here — extend deliberately):
  - `rm -rf` (any flag order containing both r and f)
  - `git reset --hard`
  - `git push --force` / `git push -f`
  - `chmod 777`
  - `dd ... of=/dev/...`
  - `mkfs`, `shutdown`, `reboot`
- Pairs with: `continue-on-block-hooks.md` (block-and-feedback semantics).

## When to Use
KlodTalk agents run inside Docker containers with `/workspace` bind-mounted from the host. The container boundary does not protect the mounted volume — a `rm -rf /workspace` from inside the agent still destroys host files. This hook is the defence-in-depth layer at the tool-call level.

## Registration
Add to `.claude/settings.json` (NOT modified by this skill — register at container build / operator deployment time):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "continueOnBlock": true,
        "hooks": [
          { "type": "command",
            "command": "bash /workspace/server/utils/hooks/pre_tool_use_guard.sh" }
        ]
      }
    ]
  }
}
```

## Critical Caveat (per instincts.md line 7)
Role YAML frontmatter currently forwards **only** `mcpServers` and `disallowedTools`. A `hooks:` key in role frontmatter is **silently ignored**. Hook registration MUST happen at the container level via `.claude/settings.json` (typically baked in by `server/run_agent.py` or the operator's deployment script). Do not attempt per-role hook registration via frontmatter.

## Behaviour
- Reads stdin JSON (`tool_name`, `tool_input.command`); uses `jq` with a raw `grep`/`sed` fallback (same defensive pattern as `post_tool_use_logger.sh`).
- Only inspects `tool_name == "Bash"`; allows everything else.
- On match: writes `Refused: destructive command pattern '<pattern>' matched -- see CLAUDE/skills/pre-tool-use-guard.md` to stderr and exits 2. Claude receives the stderr as feedback (via `continueOnBlock`) and can adjust.
- On no match: exits 0.

## Extending the Deny-List
Keep it narrow. False positives that block legitimate commands are worse than the hook not existing. When adding a pattern, prefer word-boundary or argument-bounded regex (`\b`, `[[:space:]]`) over loose substrings.

## Source
disler/claude-code-hooks-mastery — https://github.com/disler/claude-code-hooks-mastery (~3,700 stars).
