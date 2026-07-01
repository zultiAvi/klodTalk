---
skill_name: sonnet-5-default-breaking-changes
triggers:
  - Adding claude-sonnet-5 to .claude/settings.json availableModels
  - Diagnosing an HTTP 400 from a thinking/budget_tokens or temperature/top_p/top_k param on Sonnet 5
  - Sizing a role prompt's token budget for a Sonnet 5 target after the v2.1.197 default flip
summary: "Claude Sonnet 5 (claude-sonnet-5) is the new Claude Code CLI default as of v2.1.197 (1M context, 128k output, promo $2/$10 per MTok through Aug 31 2026). It is intentionally ABSENT from KlodTalk availableModels pending a sampling-param audit. Breaking vs Sonnet 4.6: adaptive thinking always-on, manual budget_tokens -> HTTP 400, non-default temperature/top_p/top_k -> HTTP 400, ~30% tokenizer inflation. Doc only."
description: "Documents the breaking changes that land when claude-sonnet-5 becomes the Claude Code CLI default in v2.1.197, and the reinstatement checklist before adding it to the availableModels allowlist. Use when adding Sonnet 5 to availableModels, diagnosing an HTTP 400 from thinking/budget_tokens or sampling params on Sonnet 5, or re-sizing role token budgets for the new tokenizer. Mirrors the fable-5-tokenizer-and-thinking pre-arming pattern."
---

# Skill: Sonnet 5 New Default & Breaking Changes (v2.1.197+)

## Why This Exists
Claude Code v2.1.197 makes **`claude-sonnet-5` the CLI default** — the `sonnet` alias
resolves to it in an unguarded CLI. KlodTalk's `enforceAvailableModels: true` correctly
blocks it today (it is **not** in `availableModels`), so no active breakage. This skill
pre-arms the night a scout recommends adding it, exactly like `fable-5-tokenizer-and-thinking.md`.

## Quick Reference
- Default as of Claude Code **v2.1.197**; `claude-sonnet-5` NOT in KlodTalk `availableModels` (safe posture).
- 1M-token native context, 128k max output; introductory **$2/$10 per MTok through Aug 31 2026**.
- `model-version-hygiene.md` still maps `sonnet` -> `claude-sonnet-4-6` (KlodTalk's pinned target).

## Breaking Changes vs Sonnet 4.6
1. **Adaptive thinking is ON by default** — cannot be disabled.
2. **Manual `thinking: {budget_tokens}` returns HTTP 400** — adaptive thinking is always-on.
3. **Non-default `temperature` / `top_p` / `top_k` return HTTP 400** (same family as Opus 4.7+).
4. **~30% tokenizer inflation** — same text emits ~30% more tokens; role budgets silently overflow.

## Reinstatement Checklist (run all before adding claude-sonnet-5 to availableModels)
1. Grep role files for sampling params: `grep -rn "temperature\|top_p\|top_k\|budget_tokens" /workspace/teams/ /workspace/server/` — remove/gate any on a Sonnet 5 path.
2. Re-audit every role prompt / context budget sized for a token count; pad +30%.
3. Add `claude-sonnet-5` to `/workspace/.claude/settings.json` `availableModels` only after 1+2.
4. Bump `model-version-hygiene.md` `sonnet` alias + Active Models table if promoting it to the KlodTalk default.

## Cross-References
- `fable-5-tokenizer-and-thinking.md` — same pre-armed breaking-change pattern (tokenizer + thinking).
- `enforce-available-models.md` — the allowlist that currently blocks Sonnet 5.
- `opus-sampling-params-deprecated.md` — the sibling HTTP-400 sampling-param restriction on Opus 4.7+.
- `model-version-hygiene.md` — the `sonnet` alias resolution this skill tracks.
- `required-minimum-version-pin.md` — the v2.1.197 floor that ships this default.

## Source
- Claude Code CHANGELOG v2.1.197 — https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md
  (github.com/anthropics/claude-code); also confirmed at
  https://platform.claude.com/docs/en/release-notes/overview (docs.anthropic.com).
