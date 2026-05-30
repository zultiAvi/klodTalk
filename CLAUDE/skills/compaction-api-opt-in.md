---
skill_name: compaction-api-opt-in
triggers:
  - Preventing context-window exhaustion in long-running KlodTalk Coder/Planner sessions
  - Opting a role/team into server-side context compaction
  - Operating Opus 4.6+ agents over multi-file refactors
summary: Set KLODTALK_CONTEXT_COMPACTION=1 on the orchestrator/container env; run_agent.py forwards it as CLAUDE_CODE_CONTEXT_COMPACTION=1 to the claude CLI. Requires Opus 4.6+ and draws from the Agent SDK credit pool.
---

# Skill: Compaction API Opt-In for Long-Running Coder/Planner Agents

## Quick Reference
- KlodTalk env var (operator-facing): `KLODTALK_CONTEXT_COMPACTION=1`
- Forwarded as: `CLAUDE_CODE_CONTEXT_COMPACTION=1` to the `claude` CLI process
- Dispatch site: `server/run_agent.py` (env-var passthrough -- mirrors the `KLODTALK_PLUGIN_DIR` pattern in `plugin-dir-dispatch.md`)
- Model requirement: Opus 4.6+ (compaction is unsupported on older models)
- Credit pool: draws from the Agent SDK credit pool starting June 15 2026 (see `agent-sdk-credit-billing.md`)
- Default: **off**. Opt-in only.

## When to Use
- A Coder agent is performing a large multi-file refactor and the session
  is hitting the context window before completion.
- A Planner agent is reasoning over a large codebase and you want it to
  survive deep exploration without context truncation.
- You have validated that the role is running on Opus 4.6+ (see
  `model-version-hygiene.md`).

## What Compaction Does

The Claude Compaction API (server-side context summarization) transparently
summarizes earlier turns of a session so the effective conversation length
is unbounded. Enabled by sending the `anthropic-beta` header (REST) or by
exporting `CLAUDE_CODE_CONTEXT_COMPACTION=1` (Claude Code CLI v2.1.x).

Trade-offs:
- **Pros:** prevents mid-task session failures on large codebases;
  reduces costly pipeline re-runs.
- **Cons:** increases per-session token usage (the summaries themselves
  cost tokens). On subscription plans after June 15 2026, this draws from
  the separate Agent SDK credit pool; monitor via `/v1/usage` or the
  Anthropic console.

## Why an Env Var (Not Frontmatter)

Per **instinct #16**, per-role config knobs in KlodTalk dispatch through
environment variables, **not** role YAML frontmatter -- `server/run_agent.py`
does not parse role frontmatter beyond `mcpServers` and `disallowedTools`
(instinct #7). Adding `context_compaction: true` to `teams/roles/coder.md`
would be silently ignored.

The contract is therefore:

1. Operator exports `KLODTALK_CONTEXT_COMPACTION=1` in the
   orchestrator/container env for the roles that should use compaction
   (Coder, Planner, long-running Reviewer over big diffs).
2. `server/run_agent.py` checks the env var at every `claude` invocation
   and, when set, forwards `CLAUDE_CODE_CONTEXT_COMPACTION=1` into the
   subprocess env so the Claude Code CLI activates the beta.

Leaving the env var unset on Reviewer/Documenter/Scout containers (whose
sessions are short) avoids unnecessary token overhead.

## Implementation in `server/run_agent.py`

The CLI subprocess receives a per-call env dict built by `_claude_env()`.
The opt-in is a small passthrough in that function:

```python
def _claude_env() -> dict:
    env = os.environ.copy()
    env.update(_claude_auth.get_env())
    if os.environ.get("KLODTALK_CONTEXT_COMPACTION", "").strip():
        env["CLAUDE_CODE_CONTEXT_COMPACTION"] = "1"
    return env
```

Empty / unset values are ignored, so the change is a no-op for existing
deployments.

## Operator Setup (per-role scoping)

Set the env var only on the containers running long-context roles. Example
docker-compose snippet for the Coder service:

```yaml
services:
  coder:
    environment:
      - KLODTALK_CONTEXT_COMPACTION=1
  planner:
    environment:
      - KLODTALK_CONTEXT_COMPACTION=1
  # Reviewer / Documenter / Scout: leave unset.
```

Or per `docker run`:

```bash
docker run -e KLODTALK_CONTEXT_COMPACTION=1 ... klodtalk-agent
```

## Verifying

Inside a Coder container after launch:

```bash
echo "${KLODTALK_CONTEXT_COMPACTION:-unset}"
```

Expected `1`. Then trigger a long session and observe (via Anthropic
console or `/v1/usage`) that earlier turns are being summarized rather
than dropped.

## Model Requirement

Compaction is available on Opus 4.6 and later. Audit your team's model
config (`teams/*.md`, `config/`) and confirm none of the long-running
roles are pinned to a retired model (see `model-version-hygiene.md` --
e.g. `claude-3-haiku-20240307` is retired April 2026; Sonnet 4 / Opus 4
`*-20250514` retire June 15 2026).

If the model is older than 4.6, the env var is silently ignored by the
CLI; the session will not benefit from compaction but will not fail.

## Credit-Pool Interaction (Post-June 15 2026)

Starting June 15 2026, `claude -p` and Agent SDK usage on Pro/Max/Team/
Enterprise subscription plans draws from a **separate** Agent SDK credit
pool (see `agent-sdk-credit-billing.md`). Compaction increases per-session
token usage, so:

- Add a pre-flight credit check before launching a long pipeline with
  compaction enabled (analogous to the RPM/TPM probe in
  `rate-limit-awareness.md`).
- For OAuth-only deployments, schedule a manual `/v1/usage` check on the
  Anthropic console before each nightly run.
- Rate limits (RPM/TPM) and credit pools are independent constraints --
  both apply.

## Related
- `precompact-context-guard.md` -- snapshot in_message.txt + progress.json
  + last 5 hook events before each compaction pass so you can diagnose
  context loss; pair with this skill on long Coder/Planner runs.
- `agent-sdk-credit-billing.md` -- the credit pool you draw from after
  June 15 2026; required reading before enabling compaction at scale.
- `plugin-dir-dispatch.md` -- the env-var-dispatch pattern this skill
  mirrors (`KLODTALK_PLUGIN_DIR` -> `--plugin-dir`).
- `model-version-hygiene.md` -- model IDs supported on Opus 4.6+.
- `rate-limit-awareness.md` -- companion preflight probe for RPM/TPM.
- `large-output-spill.md` -- a different mitigation (output size, not
  context tokens); compaction does not replace it.

## Source
- docs.anthropic.com -- "Compaction API Beta (Server-Side Context
  Summarization)" -- https://docs.anthropic.com/en/release-notes/api
  (current beta on Opus 4.6+, 2026).
