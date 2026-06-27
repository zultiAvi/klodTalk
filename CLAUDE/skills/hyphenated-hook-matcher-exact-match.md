---
skill_name: hyphenated-hook-matcher-exact-match
triggers:
  - Adding a hook in settings.json for an MCP server whose name contains a hyphen
  - A matcher like `mcp__name-with-hyphen` stops firing after upgrading the CLI to 2.1.195
  - Deciding the right matcher pattern for a tool/MCP server name that contains hyphens
summary: 'From Claude Code 2.1.195 hook matchers with hyphenated identifiers (e.g. `code-reviewer`, `mcp__brave-search`) exact-match instead of accidentally substring-matching; a plain `mcp__brave-search` matcher now matches ONLY that exact tool name — use the `mcp__brave-search__.*` wildcard to match all tools from a hyphenated MCP server. KlodTalk has zero hyphenated matchers today (all use `""`), so this is forward-looking.'
description: "Documents the Claude Code 2.1.195 breaking change to hook matcher semantics for hyphenated identifiers. Before 2.1.195 a hyphenated matcher accidentally substring-matched partial tool names; from 2.1.195 it exact-matches, so a plain `mcp__server-name` matcher only fires for a tool literally named that. Use this when adding a hook for an MCP server with hyphens in its name, when a hyphenated matcher silently stops firing after a CLI upgrade, or when choosing the correct matcher pattern for hyphenated tool/server names."
---

# Skill: Hyphenated Hook `matcher` Exact-Match (CLI 2.1.195)

## Quick Reference
- Before **2.1.195**: hyphenated identifiers in a `matcher` (e.g. `mcp__brave-search`) accidentally **substring-matched** — they fired for partial/related tool names.
- From **2.1.195** (KlodTalk's pinned floor): hyphenated matchers **exact-match** only.
- A plain `"matcher": "mcp__brave-search"` now matches **only** the tool literally named `mcp__brave-search`, NOT all tools from the `brave-search` server.
- To match **all tools** from a hyphenated MCP server, use the wildcard: `"matcher": "mcp__brave-search__.*"`.

## When to Use
Whenever you add a hook entry to `/workspace/.claude/settings.json` whose `matcher`
targets an MCP server or tool name containing a hyphen (`code-reviewer`,
`mcp__brave-search`, etc.), or when a previously-working hyphenated matcher stops
firing after the CLI advances to 2.1.195.

## The Change (2.1.195)
The 2.1.195 changelog fixed hook matchers with hyphenated identifiers accidentally
substring-matching — they now exact-match. The "match every tool from this server"
semantics that the old substring behavior gave for free must now be expressed
explicitly with the `__.*` wildcard suffix.

## KlodTalk Convention
- KlodTalk currently has **no hyphenated matchers** — every active hook uses
  `"matcher": ""` (all tools/events), so nothing is broken by this change today.
- When adding a hook for a hyphenated MCP server, always use the
  `mcp__server-name__.*` wildcard for "all tools from this server" semantics; never
  rely on bare `mcp__server-name` to match more than that exact name.

## Cross-References
- `hook-comma-matcher-syntax.md` — the comma-separated tool-list matcher footgun (2.1.191).
- `required-minimum-version-pin.md` — the 2.1.195 floor that makes this exact-match behavior the norm.
