---
skill_name: ultrareview-integration
triggers:
  - Pre-merge review of a large or high-risk diff
  - Reviewer role wants deeper automated bug-hunting coverage
  - User explicitly opts into a paid deep review
summary: Optionally invoke `claude /ultrareview` -- a cloud-based multi-agent bug-hunting fleet ($5-$20/run) -- as an opt-in deeper pass for the Reviewer role. Standard Claude Code CLI only (not Bedrock/Vertex/Foundry/ZDR).
---

# Skill: /ultrareview Integration (Opt-In Deep Review)

## Quick Reference
- Command: `claude /ultrareview` (run inside the agent container at the repo root).
- Cost: ~$5-$20 per invocation. NOT for every pipeline run.
- Mode constraint: standard Claude Code CLI only -- unsupported under Bedrock, Vertex, Foundry, or Zero Data Retention.
- Strictly opt-in: never wire into the mandatory pipeline; require an explicit user/operator flag.

## When to Use
- Pre-merge sanity check on large diffs (rule of thumb: >300 changed lines or touching security-sensitive paths).
- High-risk changes: auth, crypto, payment, container build files, server message routing.
- A second opinion when the Reviewer role flags a complex issue it is unsure about.

## When NOT to Use
- Routine documentation-only or skill-file commits.
- Inside any pipeline run that is intended to be free/cheap (the nightly scout pipeline, for example).
- When the agent container is configured against Bedrock/Vertex/Foundry endpoints.

## Instructions

1. Confirm opt-in: the user or team config has explicitly requested `/ultrareview` for this run. Default is OFF.
2. Confirm the runtime is standard Claude Code CLI (not Bedrock/Vertex/Foundry/ZDR). If unsure, skip.
3. From the agent container, with the working tree at the commit-to-review, run:
   ```bash
   claude /ultrareview
   ```
4. Capture the slash-command output and attach the key findings to `reviewer_output.txt` under a clearly labelled `## /ultrareview Findings` section. Apply the standard severity prefixes (`BLOCKER:`, `WARNING:`, `SUGGESTION:`) to anything you forward.
5. Treat `/ultrareview` output as advisory input to the human Reviewer role, not as a replacement for it.

## Related
- `teams/roles/reviewer.md` -- the natural integration point; reviewer remains the authoritative output.
- `rate-limit-awareness` -- helpful context on cost-bearing operations.

## Source
Claude Code /ultrareview Slash Command -- https://code.claude.com/docs/en/changelog
