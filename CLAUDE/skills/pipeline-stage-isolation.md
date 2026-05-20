---
skill_name: pipeline-stage-isolation
triggers:
  - Authoring an Orchestrator or `run_claude_team.sh` caller that sequences pipeline stages
  - A nightly unattended run where one stage failure must not cascade to abort the whole pipeline
  - Designing per-stage retry / partial-result behaviour for plan-code-review pipelines
summary: "Each pipeline stage writes `.klodTalk/team/current/stage_<role>_result.txt` with `OK` or `FAILED: <reason>`; the Orchestrator reads it before launching the next stage so failures isolate instead of cascading."
---

# Skill: Cascade-Failure Isolation for Pipeline Stages

## Quick Reference
- Per-stage result file: `.klodTalk/team/current/stage_<role>_result.txt`.
- Contents: first line is `OK` or `FAILED: <short reason>`; remaining lines are optional context.
- Orchestrator (or `run_claude_team.sh` wrapper) checks this file before dispatching the next stage.
- Result files are ephemeral, never committed (under gitignored `.klodTalk/`).
- This pattern is a convention only -- it does NOT modify `server/server.py` or `session_manager.py`.

## When to Use
KlodTalk nightly runs are unattended. Without per-stage isolation, a single transient failure (rate-limit hit, Docker restart, OOM in one role) silently aborts the whole pipeline -- producing no partial result and wasting the run. Use this skill whenever you set up a multi-stage pipeline (nightly-scout, nightly-scout-with-tests, optimizer, plan-code-qa-review) that must continue or degrade gracefully on a single-stage failure.

## Instructions

### Stage producer discipline
At the end of every role's run, before exiting:
```bash
result_file=".klodTalk/team/current/stage_${ROLE}_result.txt"
if [ "$STAGE_OK" = "1" ]; then
  echo "OK" > "$result_file"
else
  echo "FAILED: $REASON" > "$result_file"
fi
```
`$REASON` should be a short tag the Orchestrator can branch on: `rate_limit`, `docker_restart`, `reviewer_below_threshold`, `tool_error`, `unknown`.

### Orchestrator gate snippet
```bash
prev_result=$(head -n 1 ".klodTalk/team/current/stage_${PREV_ROLE}_result.txt" 2>/dev/null || echo "MISSING")
case "$prev_result" in
  OK)
    launch_stage "$NEXT_ROLE" ;;
  FAILED:*rate_limit*|FAILED:*docker_restart*)
    # transient -- one automatic retry with 30s back-off
    sleep 30 && retry_stage "$PREV_ROLE" ;;
  FAILED:*reviewer_below_threshold*|FAILED:*tool_error*|MISSING|FAILED:*)
    # logic failure or missing result -- record partial summary and exit cleanly
    write_partial_summary "$PREV_ROLE" "$prev_result"
    exit 0 ;;
esac
```

### Retry policy
- Transient (`rate_limit`, `docker_restart`): one automatic retry after 30s back-off.
- Logic (`reviewer_below_threshold`, `tool_error`): no retry -- record partial and stop.
- Missing result file: treat as logic failure (the stage crashed without writing) -- no retry.

### Partial-summary contract
On a non-retried failure, the Orchestrator writes a brief summary to `out_message.txt` indicating which stages completed (`stage_<role>_result.txt == OK`), which failed, and where the partial artefacts live. This gives the human running the nightly something actionable instead of silence.

### Gitignore
`.klodTalk/` is already gitignored, so `stage_*_result.txt` files stay local. Do not add explicit `git add` lines for them in any role.

## Related
- `reviewer-exit-condition-scoring.md` -- the scoring gate that produces a `FAILED: reviewer_below_threshold` verdict.
- `rate-limit-awareness.md` -- distinguishing transient rate-limit failures from logic failures.
- `pipeline-handoff.md` -- structured handoff summary written alongside the result file on `OK`.
- `large-output-spill.md` -- a missing spill file is a stage failure (`tool_error`).

## Source
open-multi-agent/open-multi-agent -- https://github.com/open-multi-agent/open-multi-agent (~6.2k stars); cascade-failure isolation pattern from its semaphore-controlled agent pool.
