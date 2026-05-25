---
skill_name: tool-search-mcp-token-reduction
triggers:
  - Configuring a role that attaches 3 or more MCP servers
  - Reducing per-run token cost on MCP-heavy roles
  - Enabling parallel tool execution for benchmark-sensitive agents
summary: "Tool Search Beta (header tool-search-2026-01-01) lets Claude discover MCP tool defs on demand, cutting tokens ~85% on MCP-heavy roles; opt-in via ANTHROPIC_BETA env var."
---

# Skill: Tool Search MCP — Token Reduction for MCP-Heavy Roles

## Quick Reference
- Beta header: `tool-search-2026-01-01`
- Pass via env: `ANTHROPIC_BETA=tool-search-2026-01-01` in the container env
- Token reduction: ~85% on roles with many MCP tool definitions
- Companion (GA): Programmatic Tool Calling — parallel tool execution
- Recommended targets: `github_scout`, `website_scout`, any role with 3+ MCP servers

## When to Use
- A role attaches more MCP servers than it actually uses each turn.
- Per-run cost on a scout / scanner role is dominated by tool-definition tokens, not by reasoning tokens.
- You want parallel tool execution for accuracy on benchmark-style tasks.

## Instructions

### Enabling Tool Search (Beta)
1. Add `ANTHROPIC_BETA=tool-search-2026-01-01` to the agent container's environment (e.g., via the launch wrapper in `server/run_agent.py`).
2. No role-file change is strictly required, but it is good practice to add a one-line note on the role's `.md` referencing this skill so future readers know the role is a Tool Search candidate.
3. Claude will then search MCP tool definitions on demand rather than loading the entire MCP tool catalog into context up front.

### Programmatic Tool Calling (GA)
- Distinct from Tool Search: PTC enables Claude to dispatch tool calls in parallel rather than sequential round-trips.
- Best paired with Tool Search on scout-style roles that fan out across many MCP servers.

### BETA CAVEAT
- Behavior may change before GA. Test on one role (e.g., `github_scout`) before enabling across all team runs.
- Some MCP servers may not advertise tool descriptions in a way the search index understands — measure token impact before/after.

## Source
- Anthropic platform docs — Programmatic Tool Calling (GA) + Tool Search (Beta): https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling (docs.anthropic.com)
