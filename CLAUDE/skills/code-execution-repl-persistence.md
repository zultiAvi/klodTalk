---
skill_name: code-execution-repl-persistence
triggers:
  - A Coder/Planner role needs to run multi-step Python/JS that reuses state across turns
  - Deciding whether to enable the server-side code-execution tool for a KlodTalk role
  - Evaluating Anthropic's `code_execution_20260120` REPL-persistence tool
summary: "Anthropic's `code_execution_20260120` server tool persists REPL state (variables, file handles, loaded data) across turns within a session; as of June 2026 it no longer requires a beta header. A Coder/Planner role can run multi-step Python/JS without re-initializing state, with results in tool-result `output` blocks. CAUTION: the exact tool ID and the no-beta-header claim are scout-reported (2026-06-18) and MUST be re-confirmed against docs.anthropic.com before relying on the identifier. Doc-only skill."
---

# Skill: Code-Execution Tool REPL Persistence

## Quick Reference
- Tool ID: **`code_execution_20260120`** *(see verification note below before relying on this exact string)*.
- Behavior: persists REPL state — variables, file handles, loaded datasets, imported modules — **across turns within the same session**.
- Beta header: **no longer required as of June 2026** *(see verification note)*.
- Results: returned in the tool-result `output` blocks.
- Supported models (as reported): `claude-fable-5`, `claude-mythos-5`, `claude-opus-4-5+`, `claude-sonnet-4-5+`.

## VERIFICATION NOTE (read before relying on the identifier)
The exact tool ID `code_execution_20260120` and the "no beta header required" claim are
**verified by website scout 2026-06-18 — re-confirm against docs.anthropic.com before
relying on the exact identifier.** API identifiers and beta-header requirements drift; do
not propagate an unverified identifier as gospel. If a call fails with an unknown-tool
error, the dated suffix is the first thing to re-check against the current release notes.

## When to Use
- A Coder or Planner role needs to run a multi-step Python/JS computation where later steps
  depend on earlier in-memory state (a loaded dataframe, an open file handle, an accumulated
  variable) and you want to avoid re-initializing that state on every turn.
- Iterative data exploration / scratch computation where a persistent REPL is more efficient
  than re-running a self-contained script each turn.

## KlodTalk Relevance
- Lets a Coder/Planner sub-agent treat the session like a live notebook instead of replaying
  setup code each turn — cheaper and faster for multi-step analysis.
- Output appears in tool-result `output` blocks, so it slots into the existing tool-result
  flow without a custom channel.

## Caution
- **Long-lived REPL state consumes context.** Accumulated variables, large loaded datasets,
  and prior outputs all stay in the session and grow the context window. For long-running
  KlodTalk container sessions this can crowd out useful context — reset or scope the REPL
  when the in-memory state is no longer needed.

## Related
- `claude-api` skill — building against the Claude API / Anthropic SDK, where this tool is configured.

## Source
docs.anthropic.com release notes, 2026-06-18 (website scout).
