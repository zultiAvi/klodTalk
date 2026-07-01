---
skill_name: opus-fast-mode-removal
triggers:
  - A role or config references speed:"fast" (fast mode) on claude-opus-4-6 or claude-opus-4-7
  - Auditing an Opus migration before the July 24 2026 fast-mode hard-removal deadline
  - A previously-working fast-mode Opus request starts erroring or silently running at standard speed
summary: "Fast mode (speed:\"fast\") is REMOVED from claude-opus-4-6 (requests silently run at standard speed) and DEPRECATED on claude-opus-4-7 with HARD REMOVAL on July 24 2026 (speed:\"fast\" on 4.7 will then error). Only claude-opus-4-8 retains fast mode. KlodTalk's opus alias already points to 4.8, so no active breakage today. Doc only."
description: "Documents the removal of Opus fast mode (speed:\"fast\") across Opus 4.6/4.7/4.8 and the July 24 2026 hard-removal deadline for Opus 4.7. Use when a role or config sets speed:\"fast\" on Opus 4.6/4.7, when auditing an Opus migration before the July 24 2026 deadline, or when a fast-mode request starts erroring or silently downgrading to standard speed."
---

# Skill: Opus Fast Mode Removal (July 24 2026 hard deadline)

## Quick Reference
- `claude-opus-4-6`: fast mode **removed** — a `speed: "fast"` request silently runs at **standard speed** (no error, no speedup).
- `claude-opus-4-7`: fast mode **deprecated** — **HARD REMOVAL on July 24, 2026**; after that date `speed: "fast"` on 4.7 will **error**.
- `claude-opus-4-8`: **retains** fast mode going forward.
- KlodTalk's `opus` alias already resolves to `claude-opus-4-8`, so there is **no active breakage today** — this closes a documentation gap and guards legacy 4.6/4.7 pins.

## When to Use
When a team definition, role file, or config still pins `claude-opus-4-6`/`claude-opus-4-7`
and sets `speed: "fast"`, or when auditing Opus usage before the July 24, 2026 deadline.

## Instructions
1. **Audit** for any fast-mode usage:
   ```
   grep -rn 'speed.*fast' /workspace/teams/ /workspace/server/ /workspace/config/
   ```
2. **Fix by target model**:
   - Targeting **Opus 4.7** with fast mode: migrate to `claude-opus-4-8` **before July 24, 2026** (only 4.8 keeps fast mode).
   - Targeting **Opus 4.6**: remove `speed: "fast"` — it is a silent no-op (request already runs at standard speed).
   - Already on **Opus 4.8** (KlodTalk's `opus` alias today): fast mode still works; no change needed.

## Cross-References
- `opus-4-7-migration.md` — the Opus 4.6→4.7 behavioral migration guide this fast-mode note extends.
- `model-version-hygiene.md` — the `opus` alias resolution (currently `claude-opus-4-8`).

## Source
- Anthropic platform release notes — https://platform.claude.com/docs/en/release-notes/overview
  (docs.anthropic.com): fast mode `speed: "fast"` removed from Opus 4.6, deprecated on Opus 4.7
  with hard removal July 24 2026, retained only on Opus 4.8.
