---
skill_name: idle-watchdog-long-session
triggers:
  - A long-running KlodTalk agent / Docker container session dies or aborts silently mid-run
  - An agent that thinks for a long time (or waits on a slow tool) is terminated and retried from scratch
  - Diagnosing premature stream termination on Claude Code CLI >= 2.1.196
summary: "Claude Code v2.1.196 turns the streaming idle watchdog ON BY DEFAULT: a session with no streamed events for 5 minutes is aborted (and may retry from scratch). KlodTalk's long-running nightly Docker agents (slow opus reasoning, long WebFetch/test waits) can be killed silently. If you see premature termination, set CLAUDE_ENABLE_STREAM_WATCHDOG=0 in the agent container env (threshold configurable via CLAUDE_STREAM_IDLE_TIMEOUT_MS)."
---

# Skill: Idle Watchdog Can Kill Long-Running KlodTalk Sessions (v2.1.196+)

## When to Use
A long-running agent session terminates silently mid-task, or a background/nightly
agent appears to restart from the original prompt for no clear reason, on a container
running Claude Code CLI >= 2.1.196. Symptom: the stream goes quiet during a long
reasoning step or a slow tool call, then the session aborts/retries.

## Why This Matters
v2.1.196 changed the **streaming idle watchdog from opt-in to ON BY DEFAULT**. The
watchdog aborts a session that emits no streamed events within its idle window.
KlodTalk's pipeline routinely has legitimately quiet stretches:
- opus coder/orchestrator turns that reason for a long time before emitting tokens,
- sub-agents blocked on a slow `WebFetch`, test run, or container build,
- background sessions waiting on a scheduled trigger.

A killed orchestrator session loses in-flight pipeline state; a killed sub-agent makes
the orchestrator see "no output" and burn a retry. This is an operational regression
introduced purely by the CLI floor bump, not by any KlodTalk code change.

## Instructions
1. **Confirm the floor**: this only applies at CLI `>= 2.1.196` (see
   `required-minimum-version-pin.md`). Below that floor the watchdog was opt-in.
2. **Mitigation — disable per container**: set the env var in the agent container, NOT
   in committed project settings (set the *enable* flag to `0` to turn the watchdog OFF):
   ```
   CLAUDE_ENABLE_STREAM_WATCHDOG=0
   ```
   Forward it the same way other `CLAUDE_*` knobs reach the container env in
   `server/run_agent.py` (the container env dict). Do NOT hardcode it globally without
   cause — keep it conditional on observed premature termination, since the watchdog is a
   legitimate hang-recovery feature for genuinely stuck sessions. The idle threshold
   itself is configurable via `CLAUDE_STREAM_IDLE_TIMEOUT_MS` (default 5 minutes /
   300000 ms) if you prefer to lengthen the window rather than disable the watchdog.
3. **Prefer a narrow fix**: if only one role (e.g. an opus coder with long quiet
   reasoning) is affected, scope the env var to that role's invocation rather than all
   agents.
4. **Do not** treat a watchdog kill as a refusal or a crash — it has no refusal
   `stop_reason`. If you see silent termination with no error, suspect the watchdog first.

## Cross-References
- `required-minimum-version-pin.md` — v2.1.196 history row documents the watchdog default-on change and this same mitigation.
- `background-agent-durability.md` — background-session survival across restarts.
- `docker-claude-stability.md` — other container-stability knobs for long-running agents.
