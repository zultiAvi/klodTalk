---
skill_name: agent-sdk-credit-billing
triggers:
  - Planning subscription-plan usage for KlodTalk pipelines
  - Diagnosing unexpected "credit exhausted" errors after June 15 2026
  - Monitoring Agent SDK credit consumption on Pro/Max/Team/Enterprise plans
summary: Starting June 15 2026, claude -p and Agent SDK usage on subscription plans draws from a separate Agent SDK credit pool — monitor via /v1/usage.
---

# Skill: Agent SDK Credit Billing

## Quick Reference
- Effective: June 15, 2026
- Affects: `claude -p` (print/pipeline mode) and Agent SDK calls on Pro/Max/Team/Enterprise plans
- Separate from interactive usage limits — has its own monthly credit pool
- Monitor: `GET /v1/usage` (requires API key); OAuth-only setups must use the Anthropic console
- Source: https://platform.claude.com/docs/en/docs/claude-code/sdk

## When to Use
Before launching long-running KlodTalk nightly pipelines after June 15 2026, when adding pre-flight checks to `run_claude_team.sh`, or when diagnosing pipeline failures that report credit exhaustion while interactive sessions still work.

## Instructions

### KlodTalk Impact
All KlodTalk pipeline execution flows through `claude -p` — `teams/run_claude_team.sh` and `server/run_agent.py` both invoke it non-interactively. After the cutover, every container launch consumes from the Agent SDK credit bucket, not the interactive bucket. Operators may see interactive sessions working fine while pipelines fail.

### Monitoring Credit Headroom
Query `GET /v1/usage` with an API key to surface Agent SDK credit remaining and the next reset timestamp. For OAuth-only deployments (no API key), credit visibility is restricted to the Anthropic console — schedule a manual check before each nightly run.

### Recommended Pre-Flight Check
Add a credit-headroom probe to the nightly pipeline preamble analogous to the RPM/TPM probe in `rate-limit-awareness.md`. Abort the pipeline early with a clear message if remaining credit is below the estimated cost of the run, rather than failing mid-pipeline.

### Interaction with Rate Limits
Rate limits (RPM/TPM) and credit pools are independent constraints — both apply simultaneously. A pipeline can pass the rate-limit probe and still fail on credit exhaustion, and vice versa. Keep both checks.

## Tooling
- `CLAUDE/skills/ant-cli-helpers.md` — the official `ant` CLI wraps `GET /v1/usage` (`ant usage`) for terminal credit checks. Note: OAuth-only installs have no API key, so credit queries remain console-only.

## Related
- `CLAUDE/skills/rate-limit-awareness.md` — RPM/TPM headroom (distinct constraint)
- `CLAUDE/skills/claude-agents-cli.md` — session launch flags
- `CLAUDE/skills/compaction-api-opt-in.md` — compaction raises per-session token usage; if opted in, plan extra headroom against this credit pool

## Source
Claude Code SDK documentation — https://platform.claude.com/docs/en/docs/claude-code/sdk (docs.anthropic.com)
