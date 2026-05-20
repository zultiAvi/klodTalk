---
skill_name: advisor-tool-usage
triggers:
  - Using the advisor tool for single-agent sessions
  - Reducing pipeline overhead for simple tasks
  - Enabling intelligent model tiering within a single agent
summary: How to use Anthropic's advisor tool (public beta) in KlodTalk single-agent sessions for lightweight tasks.
---

# Skill: Advisor Tool Usage

## Quick Reference
- Beta header: `advisor-tool-2026-03-01`
- Best team: `solo-general` (single-agent, no pipeline overhead)
- Trigger: IS_SIMPLE=true tasks where the full team pipeline is overkill
- Auth: generation-time feature — no separate API key required
- Status: **Public Beta** (April 2026) — behavior may change

## When to Use

Use the advisor tool when:
- The task is classified as SIMPLE by the Planner (single file, trivial change)
- The user has selected the `solo-general` team
- You want a high-intelligence second opinion mid-generation without spawning an additional Docker container
- Latency and token cost matter more than maximum thoroughness

Do NOT use the advisor tool for:
- COMPLEX tasks requiring multi-file coordination (use the full team pipeline)
- Security-sensitive changes (always route through the dedicated security_reviewer role)
- Tasks that already have a full team assigned (the Planner+Coder+Reviewer pipeline is already a better advisor split)

## Background

Anthropic's advisor tool (public beta, April 2026) pairs a fast executor model with a higher-intelligence advisor model that provides strategic guidance mid-generation. This is a generation-time capability — it does not require a REST API call or a second Docker container.

KlodTalk already approximates this pattern with the Planner+Coder role split: the Planner (Opus) provides strategic guidance and the Coder (Opus/Sonnet) executes. For single-agent sessions (`solo-general` team), the advisor tool offers the same benefit within one agent invocation.

## Integration with KlodTalk

The advisor tool is a **generation-time feature**, not a server-side REST endpoint. It works transparently within a Claude Code CLI session — no changes to `server/`, `Dockerfile.agent`, or MCP configs are needed.

### Recommended Team for Advisor-Eligible Tasks

The `solo-general` team (single agent, no pipeline) is the natural home for advisor-tool-eligible tasks:
- Task is SIMPLE (`IS_SIMPLE=true` in plan_meta.txt)
- User does not need the full Plan→Code→QA→Review cycle
- Fast turnaround is prioritized over thoroughness

### How to Enable (per session)

The advisor tool is activated via the `advisor-tool-2026-03-01` beta header on API requests. In KlodTalk's OAuth auth mode, the header is passed at the CLI invocation level — consult the Anthropic migration guide before enabling in production.

**Important**: KlodTalk pins Dockerfile.agent to a specific Claude Code CLI version. Do not modify the Dockerfile to enable beta features without explicit operator approval.

## Limitations (Beta)

- Behavior and API contract may change before GA
- Token usage for advisor calls is metered separately from executor tokens
- Not compatible with `disableSkillShellExecution=true` sessions (no effect, not a shell skill)
- The advisor model selection is managed by Anthropic infrastructure — you cannot specify which advisor model is used

## References

- Advisor tool docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool
- Related team: `teams/teams/solo-general.md`
- Related skill: `CLAUDE/skills/rate-limit-awareness.md` (advisor calls count toward rate limits)
