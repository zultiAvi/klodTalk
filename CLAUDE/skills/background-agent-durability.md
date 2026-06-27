---
skill_name: background-agent-durability
triggers:
  - A background agent disappears from the `claude agents` list or loses its data
  - A background agent daemon becomes unreachable after a control-socket failure
  - Reopening a crashed background task shows a blank screen for several seconds
  - Running KlodTalk agents in a mixed CLI-version host/container environment
summary: 'Claude Code 2.1.195 ships three background-agent durability fixes — background jobs no longer disappear/lose data when written by a newer CLI version, daemons no longer run unreachable when the control socket fails (which blocked restarts), and crash-reopen no longer shows a blank screen for up to 5s; all require the >= 2.1.195 floor and protect KlodTalk long-lived nightly/Docker sessions whose state `post_session_snapshot.sh` and `subagent_lifecycle_logger.sh` depend on.'
description: "Documents the three background-agent durability fixes landed in Claude Code 2.1.195 and why they matter for KlodTalk's long-running nightly-pipeline and Docker-isolated agent sessions. Use this when a background agent vanishes from `claude agents`, loses data after a CLI upgrade, becomes unreachable after a control-socket failure, or shows a blank screen when reopening a crashed task, especially in a mixed host/container CLI-version environment."
---

# Skill: Background-Agent Durability Fixes (CLI 2.1.195)

## Quick Reference (all require CLI >= 2.1.195)
1. **Data-loss fix**: background jobs no longer disappear from `claude agents` or lose data when written by a *newer* Claude Code version.
2. **Daemon-unreachable fix**: background agent daemons no longer run unreachable when the control socket fails to start (this previously blocked restarts).
3. **Blank-screen-on-reopen fix**: reopening a crashed background task no longer shows a blank screen for up to 5 seconds before its restart.

## When to Use
When a KlodTalk background agent vanishes from `claude agents`, loses its state,
becomes unreachable, or shows a blank reopen screen — or when reasoning about agent
state durability in a mixed host/container CLI-version deployment.

## The Mixed-Version Data-Loss Scenario
If the host CLI writes background-agent state in a newer on-disk format than the
container's CLI floor understands, the job could silently disappear or lose data on
read. Pinning the floor to **>= 2.1.195** (see `required-minimum-version-pin.md`)
ensures host and container share a compatible format so state survives the round trip.

## KlodTalk Relevance
- KlodTalk's nightly-scout pipeline and Docker-isolated agents run as long-lived
  sessions; correctness depends on the agent not becoming unreachable mid-run.
- The `post_session_snapshot.sh` and `subagent_lifecycle_logger.sh` hooks depend on
  session/agent state being intact through lifecycle events — these fixes protect that.
- If a nightly agent vanishes unexpectedly, check `claude agents` and verify the
  container's CLI version meets the 2.1.195 floor before chasing a KlodTalk-side bug.

## Cross-References
- `required-minimum-version-pin.md` — the 2.1.195 floor that guarantees these fixes.
- `subagent-lifecycle-hooks.md` — the lifecycle hooks whose state durability these fixes back.
