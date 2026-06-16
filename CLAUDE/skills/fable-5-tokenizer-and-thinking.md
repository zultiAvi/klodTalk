---
skill_name: fable-5-tokenizer-and-thinking
triggers:
  - Reinstating claude-fable-5 (or claude-mythos-5) into availableModels after suspension lifts
  - Sizing a role prompt's token budget for a Fable 5 / Mythos 5 target
  - Diagnosing an HTTP 400 from a thinking/budget_tokens parameter on Fable 5
summary: "Fable 5 / Mythos 5 use the Opus 4.7 tokenizer (~30% MORE tokens for the same text) and force always-on adaptive thinking — `thinking:{type:disabled}` and manual `budget_tokens` return HTTP 400. Re-audit role token budgets (+30%) and strip thinking params before re-adding them to availableModels. Doc only."
---

# Skill: Fable 5 / Mythos 5 Tokenizer & Thinking Gotchas

## Why This Exists
`claude-fable-5` / `claude-mythos-5` are currently **suspended** (see
`model-suspension-fable-mythos-5.md`). Reinstatement is expected. The night they
return, a KlodTalk scout will recommend re-adding them to `availableModels` — and
will hit two non-obvious failure modes unless pre-armed here.

## Gotcha 1 — Opus 4.7 Tokenizer (+~30% tokens)
- Fable 5 / Mythos 5 use the **Opus 4.7 tokenizer**, which emits **~30% MORE tokens
  for the same prompt text** than Sonnet / pre-4.7 models.
- Any KlodTalk role prompt sized for a specific token count (or any code that budgets
  context length) will **silently overflow by ~30%** on Fable 5 even though the text
  is unchanged.
- Before adding Fable 5 to the allowlist, re-audit every role prompt that assumes a
  token budget and pad it by +30% (or shrink the prompt) for the Fable 5 path.

## Gotcha 2 — Always-On Adaptive Thinking (HTTP 400)
- Fable 5 forces **adaptive thinking always-on**. Passing `thinking: {type: "disabled"}`
  or a manual `budget_tokens` returns **HTTP 400**, not a silent downgrade.
- KlodTalk code or roles that pass `budget_tokens: 0` (see `compaction-api-opt-in.md`)
  or `thinking: disabled` must **gate Fable 5 out of those code paths** — those
  parameters are illegal on Fable 5.

## REINSTATEMENT CHECKLIST (run all before re-adding Fable 5)
1. Add `claude-fable-5` back to `/workspace/.claude/settings.json` `availableModels`
   (only once the suspension is confirmed lifted — see `model-suspension-fable-mythos-5.md`).
2. Re-audit every role prompt / context-budget sized for a token count; pad +30% for
   the Fable 5 path.
3. Grep for `thinking` / `budget_tokens` in any Fable 5 code path; ensure none reach
   Fable 5 (they 400).
4. Confirm `enforceAvailableModels` still lists only currently-valid IDs
   (see `enforce-available-models.md`).

## Cross-References
- `model-suspension-fable-mythos-5.md` — the suspension this skill pre-arms reinstatement for.
- `enforce-available-models.md` — the allowlist to update on reinstatement.
- `model-version-hygiene.md` — notes adaptive thinking but NOT the +30% token impact this skill adds.
- `compaction-api-opt-in.md` — the `budget_tokens` path that must gate Fable 5 out (HTTP 400).

## Source
- Anthropic API Release Notes — https://platform.claude.com/docs/en/release-notes/api
  (platform.claude.com, 2026-06-09): Fable 5 / Mythos 5 use the Opus 4.7 tokenizer
  (~30% more tokens) and reject `thinking: disabled` / manual `budget_tokens` with HTTP 400.
