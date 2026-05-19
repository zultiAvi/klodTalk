---
skill_name: canary-phrase-guard
triggers:
  - Authoring a PostToolUse hook that should refuse placeholder/stub code in Write/Edit output
  - Diagnosing a Reviewer pass that approved files containing `raise NotImplementedError` or `# TODO:`
  - Hardening nightly Coder runs against false-positive completions
summary: "PostToolUse `Write`/`Edit` hook with `continueOnBlock: true` that scans tool input for canary phrases (`raise NotImplementedError`, `# TODO:`, `pass  # placeholder`, etc.) and exits non-zero with a stderr reason so Claude is forced to implement before continuing. Capped at 3 consecutive blocks per file to avoid the 8-block Stop-hook termination."
---

# Skill: Canary-Phrase Guard (PostToolUse Quality Regression Detection)

## Quick Reference
- Hook script: `server/utils/hooks/canary_phrase_guard.sh`
- Hook type: `PostToolUse` with `"matcher": "Write"` (and optionally `"Edit"`)
- Setting: `"continueOnBlock": true` (Claude Code v2.1.139+) so the rejection reason is fed back to Claude
- Exit codes: `0` allow, `2` block with stderr reason
- Per-file block cap: 3 (stays well under the Stop-hook 8-block cap from `stop-hook-block-cap.md`)
- Counter file: `/tmp/canary_block_count_${CLAUDE_CODE_SESSION_ID}_<sha1(file_path)>`

## When to Use
- The team pipeline includes a Coder step that may produce placeholder code which would pass file-structure-only review.
- You want a deterministic gate that complements `reviewer-exit-condition-scoring.md` by catching placeholders before they reach the Reviewer.
- The hook script must NOT replace human review -- it is a fast, narrow regex filter.

## Default Canary Phrase List
The hook matches case-sensitive (anchored with word boundaries where appropriate):
- `raise NotImplementedError`
- `# TODO:` and `# TODO ` and `// TODO:` and `/* TODO */`
- `pass  # placeholder`
- `pass  # implement`
- `TODO: implement`
- `FIXME:`
- `XXX:` (standalone marker)

The list is narrow on purpose -- common false positives (e.g., `TODO` inside a docstring describing the project's roadmap) are tolerated to avoid blocking legitimate work.

## Registration Snippet
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "continueOnBlock": true,
        "hooks": [
          { "type": "command", "command": "bash /workspace/server/utils/hooks/canary_phrase_guard.sh" }
        ]
      },
      {
        "matcher": "Edit",
        "continueOnBlock": true,
        "hooks": [
          { "type": "command", "command": "bash /workspace/server/utils/hooks/canary_phrase_guard.sh" }
        ]
      }
    ]
  }
}
```

## Behavior

1. Read the tool-call JSON from stdin.
2. If `tool_name` is not `Write` or `Edit`, exit 0.
3. Extract the candidate content:
   - For `Write`: `tool_input.content`
   - For `Edit`: `tool_input.new_string`
4. If empty, exit 0.
5. Match against the canary regex list. On any match:
   - Increment the per-file block counter at `/tmp/canary_block_count_${CLAUDE_CODE_SESSION_ID}_<sha1(file_path)>`.
   - If the counter is `<= 3`: print `CANARY DETECTED: '<phrase>' in <file_path> -- implement before continuing (block N/3)` to stderr, exit 2.
   - If the counter is `> 3`: print one pass-through warning to stderr, log a `canary_cap_reached` event to `hook_events.jsonl`, exit 0.
6. Exit 0 otherwise.

## Cross-Reference
- `continue-on-block-hooks.md` -- the v2.1.139+ mechanism this hook relies on.
- `stop-hook-block-cap.md` -- the 8-block Stop-hook ceiling that motivates the per-file cap of 3.
- `hook-event-logging.md` -- the cap-reached pass-through event goes into the same JSONL log.
- `placeholder-guard.md` -- the pre-commit (offline) cousin; this skill is the inline (online) enforcement variant.

## Source
mann1x/claude-hooks -- https://github.com/mann1x/claude-hooks (stop-phrase canary detection / quality regression detection by effort level).
