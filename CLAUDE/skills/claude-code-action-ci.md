---
skill_name: claude-code-action-ci
triggers:
  - Adding an automated PR review gate via GitHub Actions
  - Wiring up anthropics/claude-code-action@v1 in a KlodTalk repo
  - Preventing feedback loops between an Action-posted comment and the agent pipeline
summary: GitHub Actions workflow uses anthropics/claude-code-action@v1 to review every PR against main; an actor guard stops feedback loops.
---

# Skill: `claude-code-action@v1` CI Review

## Quick Reference
- Workflow file: `.github/workflows/claude-code-review.yml`
- Action: `anthropics/claude-code-action@v1` (Anthropic-official, v1.0 GA May 2026)
- Trigger: `pull_request` events `opened` and `synchronize` targeting `main`
- Secret: `ANTHROPIC_API_KEY` -- repository secret, *not* committed
- Loop guard: `if: github.actor != 'claude-code[bot]'`

## When to Use
- A repository under KlodTalk needs an automated review gate before human merge.
- PRs raised by the nightly pipeline (`system_nightly_github_check` and friends) need a fast second-opinion review without spinning up the Docker team pipeline.
- You want PR-time security/correctness feedback alongside the existing post-merge `system_routine` reviewer.

## Workflow Anatomy

```yaml
on:
  pull_request:
    types: [opened, synchronize]
    branches: [main]

jobs:
  review:
    if: github.actor != 'claude-code[bot]'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0, ref: ${{ github.event.pull_request.head.sha }} }
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            <review instructions, scoped to KlodTalk CLAUDE.md conventions>
```

`fetch-depth: 0` is required so the action can diff the PR base against the head.

## Secret Setup (Operator, One-Time)

1. Repo Settings -> Secrets and variables -> Actions -> New repository secret.
2. Name: `ANTHROPIC_API_KEY`. Value: a valid Anthropic API key with code-review scope.
3. Optionally restrict the secret to the `main` branch protection ruleset so forks cannot read it via fork PRs (the workflow above does not run on forks for that reason -- `pull_request` events from forks do not receive secrets).

## Feedback Loop Prevention

The action posts findings as a PR comment via the `claude-code[bot]` GitHub App actor. Two safeguards stop the comment from re-triggering the agent pipeline:

1. **Workflow level** -- `if: github.actor != 'claude-code[bot]'` ensures the action skips its own comment-triggered runs.
2. **KlodTalk pipeline level** -- The GitHub scout role (see `github-mcp-scout.md`) must filter out PR comments authored by `claude-code[bot]` when summarising new repository activity, otherwise the nightly_scout team would treat the action's review as a fresh signal and ingest it as an idea.

## Prompt Scoping

Keep the prompt short and reference the codebase's own `CLAUDE.md` files rather than restating conventions in the workflow. The action checks the repo out with `fetch-depth: 0`, so it can read `CLAUDE.md`, `server/CLAUDE.md`, etc. directly.

## Why an Action, Not a Container

KlodTalk's existing review path is a Docker container running the Reviewer role from `teams/roles/reviewer.md`. The action complements that:

| Concern | Container pipeline | claude-code-action |
|---------|--------------------|--------------------|
| Trigger | Human via WebSocket | GitHub PR event |
| Latency | Minutes (image start + multi-role) | Seconds-to-a-minute |
| Cost | Docker host runtime | GitHub Actions minutes + API tokens |
| Where the output lands | `out_message.txt` + WebSocket | PR comment |
| Best for | Substantial code generation | Lightweight per-PR review gate |

Run both; they catch different classes of problems.

## Related
- `gh-skill-lifecycle.md` -- complementary skill-installation CLI tooling.
- `github-mcp-scout.md` -- the scout must ignore `claude-code[bot]` comments to avoid feedback loops.
- `placeholder-guard.md` -- the action's prompt should call out the same patterns the Reviewer role checks.

## Source
- anthropics/claude-code-action v1.0 release -- https://github.com/anthropics/claude-code-action/releases (Official Anthropic repo, May 2026)
