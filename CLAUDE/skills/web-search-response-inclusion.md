---
skill_name: web-search-response-inclusion
triggers:
  - Building a multi-turn web-research loop via the Claude API or Agent SDK
  - Reducing token cost from accumulated web_search / web_fetch result blocks
  - Migrating KlodTalk scouts off the CLI WebSearch tool onto the SDK
summary: "The web_search_20260318 / web_fetch_20260318 server tools accept a response_inclusion parameter that drops already-consumed result blocks from the API response, cutting tokens in multi-turn research loops with no beta header; this applies to the API/SDK path, NOT the Claude Code CLI's built-in WebSearch tool that KlodTalk scouts use today."
---

# Skill: web_search / web_fetch response_inclusion

## Quick Reference
- Tools: `web_search_20260318`, `web_fetch_20260318` now accept a `response_inclusion` parameter.
- Effect: drops consumed result blocks from the API response so they don't re-accumulate across turns, cutting tokens in multi-turn research loops.
- No beta header required.
- IMPORTANT: KlodTalk scouts use the Claude Code CLI's built-in `WebSearch` tool, NOT direct API calls — so this is an API/SDK-level option, not a CLI knob.

## When to Use
- Only relevant when KlodTalk drives agents via the API / Agent SDK path (e.g. a structured `messages` session) rather than the CLI `-p` shim.
- Treat as FUTURE DIRECTION pending an SDK migration (same framing as `btw-mid-conversation-system-message.md`): the website/github scouts cannot set this today because the CLI tool exposes no such parameter.

## Instructions
When/if KlodTalk drives a research loop through the API or Agent SDK, set `response_inclusion` on the `web_search_20260318` / `web_fetch_20260318` tool config so consumed result blocks are dropped from subsequent responses. Until then, no action — the CLI WebSearch tool ignores it.

## Cross-References
- `tool-search-mcp-token-reduction.md` — companion token-reduction lever for MCP-heavy roles.
- `btw-mid-conversation-system-message.md` — same "future direction pending SDK migration" framing.

## Source
Claude API Release Notes 2026-06-11 — https://platform.claude.com/docs/en/release-notes/overview (docs.anthropic.com)
