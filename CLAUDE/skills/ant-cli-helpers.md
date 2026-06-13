---
skill_name: ant-cli-helpers
triggers:
  - Counting tokens or estimating cost for a request before launching a KlodTalk pipeline
  - Inspecting a Claude session or managed-agent state from the terminal
  - Checking remaining Agent SDK credit headroom after June 15 2026
summary: "Official Anthropic `ant` Go CLI exposes token-count, session inspection, and usage endpoints from the terminal; for OAuth-only KlodTalk installs (no API key) `/v1/usage` and credit balances are NOT visible — same limit as the console."
---

# Skill: `ant` CLI Helpers

## Quick Reference
- Repo: anthropics/anthropic-cli — https://github.com/anthropics/anthropic-cli (official, MIT)
- Install: `go install github.com/anthropics/anthropic-cli/cmd/ant@latest` or `brew install anthropics/tap/ant`
- Auth: reads `ANTHROPIC_API_KEY` from the env. OAuth-only deployments have no key → usage/credit endpoints are unavailable.

## When to Use
- Pre-flight token counting / cost estimate before a KlodTalk nightly run.
- Inspecting a session or managed-agent state without a custom script in `helpers/`.
- Checking Agent SDK credit headroom (only when an API key is present).

## Instructions

### Token counting
```bash
ant tokens count --model claude-opus-4-8 --file in_message.txt
```
Use the count to estimate per-step cost before launching a long pipeline.

### Session inspection
```bash
ant sessions list            # enumerate sessions
ant sessions get <session-id>  # inspect one session's state
```
Useful for debugging a stuck or unexpectedly-billed run.

### Credit / usage (API key required)
```bash
ant usage get   # wraps GET /v1/usage — Agent SDK credit remaining + reset
```
This is the tooling path for the credit check described in `agent-sdk-credit-billing.md`.

## IMPORTANT Caveat — OAuth-only installs
KlodTalk authenticates Claude Code via browser OAuth, so most installs have **no `ANTHROPIC_API_KEY`**. In that case `ant usage` and any credit-balance query have the **same visibility limit as the Anthropic console** — they require an API key. Token counting still works locally with a key; session/usage endpoints do not without one. Do not assume `ant` can read credits on an OAuth-only deployment.

## Related
- `CLAUDE/skills/agent-sdk-credit-billing.md` — the June 15 2026 Agent SDK credit pool this CLI helps monitor.
- `CLAUDE/skills/claude-agents-cli.md` — session launch flags.

## Source
anthropics/anthropic-cli — https://github.com/anthropics/anthropic-cli (official Anthropic Go CLI, MIT)
