---
skill_name: claude-prompt-stdin-arg-max
triggers:
  - Invoking `claude -p` from a shell script with a large composed prompt
  - Diagnosing "Argument list too long" (E2BIG) from /usr/bin/claude
  - Adding a new agent runner that bundles orchestrator + team + roles + skills
summary: Pass large `claude -p` prompts via stdin (with a `mktemp` temp file and EXIT trap) to avoid Linux ARG_MAX (~2 MB).
---

# Skill: Pass Large `claude -p` Prompts via stdin

## Quick Reference
- Symptom: `/usr/bin/claude: Argument list too long`
- Root cause: Linux kernel `ARG_MAX` (~2 MB) caps total `argv + envp` bytes.
- Fix: omit positional/`-p` value, redirect prompt from a temp file to stdin.

## When to Use
When a shell script invokes `claude -p "$PROMPT"` and `$PROMPT` is composed
from multiple files (orchestrator.md + team .md + role .md bundle + skills
bundle + user request). KlodTalk's `teams/run_claude_team.sh` hit this once
the skill bundle grew. Any future agent runner that concatenates large
markdown chunks for the prompt is vulnerable.

## The Pattern

```bash
# Write the composed prompt to a temp file and redirect to stdin.
# Avoids ARG_MAX when "$PROMPT" exceeds ~2 MB (orchestrator + team + roles +
# skills + user request).
PROMPT_FILE=$(mktemp -t klodtalk_prompt.XXXXXX)
trap 'rm -f "${PROMPT_FILE}"' EXIT
printf '%s' "${PROMPT}" > "${PROMPT_FILE}"

claude \
    --model "${CLAUDE_MODEL}" \
    --dangerously-skip-permissions \
    --output-format json \
    -p \
    < "${PROMPT_FILE}" \
    > "${CLAUDE_OUTPUT_FILE}" || CLAUDE_EXIT=$?
```

## Rules
- Use `printf '%s'`, not `echo` — avoids appended newline and `\` ambiguity.
- Keep `-p` (print mode) but DROP the positional/argument prompt. Claude reads
  stdin when `-p` is present without a positional prompt.
- Always `trap 'rm -f "$PROMPT_FILE"' EXIT` so the temp file is removed on
  normal exit, signal, or `set -e` abort.
- Don't try `--prompt-file` — the CLI (v2.x) doesn't expose one; stdin is the
  documented channel.
- Keep `> "${CLAUDE_OUTPUT_FILE}"` separate from the input redirection.

## Related Sites in This Repo
- `teams/run_claude_team.sh` (fixed)
- `server/run_agent.sh` — three more `claude ... -p "$PROMPT"` sites
  (review/confirm/execute modes). Prompts are smaller today, but apply the
  same pattern if you see the error there or anticipate large diffs.
