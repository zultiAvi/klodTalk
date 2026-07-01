---
skill_name: opus-4-7-migration
triggers:
  - Switching a role from claude-opus-4-20250514 to claude-opus-4-7
  - Context-window overflow appearing after an Opus model swap
  - Role output volume or literal-instruction behavior changes after migration
summary: Behavioral migration guide for Opus 4.6 to Opus 4.7 — tokenizer inflation, higher output volume at high effort, and stricter literal instruction following.
---

# Skill: Opus 4.7 Behavioral Migration

## Quick Reference
- Scope: behavioral changes only — model ID swap is in `model-version-hygiene.md`
- Tokenizer inflation: same input maps to 1.0x to 1.35x more tokens (content-type dependent)
- Higher output volume at `effort: high`
- Stricter literal instruction interpretation — loose phrasing now taken at face value
- Fast mode (`speed: "fast"`) is deprecated on Opus 4.7; hard removal July 24, 2026. Only Opus 4.8 retains it. See `opus-fast-mode-removal.md`.
- Deadline: before June 15 2026 (Opus 4.6 retirement)
- Source: https://www.anthropic.com/news/claude-opus-4-7 (2026-04-16)

## When to Use
After (or alongside) the mechanical model-ID swap covered by `model-version-hygiene.md`, when a previously-stable Opus role starts overflowing context, producing longer outputs, or interpreting prompts more rigidly than before.

## Instructions

### Tokenizer Inflation (up to 1.35x)
Audit role prompts in `teams/roles/` for length. Any role whose system prompt plus typical context was near the context window may now overflow. Run each Opus role in isolation with `--model claude-opus-4-7` against a known input and watch for context-window warnings. Trim or restructure prompts where needed.

### Higher Output Volume at High Effort
Roles configured with `effort: high` (or otherwise reasoning-heavy) produce more tokens per response on 4.7. Downstream parsers that consume `out_message.txt` or `coder_output.txt` must handle longer payloads without truncation. Validate parser behavior on at least one full pipeline run before relying on the new model.

### Stricter Literal Instruction Following
Review role prompts for loose phrasing such as "roughly", "if possible", "try to", "feel free to". Opus 4.7 interprets these more literally and may produce unexpected behavior. Replace with explicit conditionals ("if X then Y, otherwise Z") or remove the ambiguity.

### Migration Checklist
1. Update model IDs per `model-version-hygiene.md`.
2. Run each Opus role in isolation with a baseline input.
3. Compare token counts and output volume against pre-migration baseline.
4. Tighten loose prompt phrasing flagged above.
5. Run the full team pipeline end-to-end before June 15 2026.

## Related
- `CLAUDE/skills/model-version-hygiene.md` — model ID swap and effort parameter
- `CLAUDE/skills/opus-sampling-params-deprecated.md` — `temperature`/`top_p`/`top_k` return a hard 400 on Opus 4.7+; remove them before migrating
- `CLAUDE/skills/orchestrator-step-edits.md` — editing role prompts safely

## Source
Claude Opus 4.7 announcement — https://www.anthropic.com/news/claude-opus-4-7 (anthropic.com/news)
