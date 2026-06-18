---
skill_name: opus-sampling-params-deprecated
triggers:
  - Adding temperature/top_p/top_k to an Opus role
  - Migrating a role to Opus 4.7 or 4.8
  - Diagnosing a 400 error on an Opus model call
  - Reviewing a role file that has sampling parameters
summary: "`temperature`, `top_p`, and `top_k` return a hard 400 on claude-opus-4-7 and later; remove all three before migrating any role to Opus 4.7/4.8 and use `effort:` for reasoning-level control instead."
---

# Skill: Opus Sampling Params Return HTTP 400 (4.7+)

## When to Use
When adding, reviewing, or migrating any role that sets `temperature`, `top_p`, or `top_k` and the target model is `claude-opus-4-7` or later (including `claude-opus-4-8`). Also when diagnosing a hard 400 on an Opus call that has no obvious cause.

## What Breaks
Setting `temperature`, `top_p`, or `top_k` to **any non-default value** returns a hard **HTTP 400** on `claude-opus-4-7` and all later Opus models (`claude-opus-4-8`, ...). There is no silent fallback — the call fails outright. A role that worked on Opus 4.6 will hard-fail the moment its model ID is bumped if any of these params are present.

## Instructions
1. Audit for the params before any Opus migration:

   ```
   grep -rn "temperature\|top_p\|top_k" /workspace/teams/ /workspace/server/
   ```

2. Fix: **remove the parameter entirely.** Opus 4.7+ ignores sampling knobs by design.
3. If the param was used to control reasoning depth, replace it with `effort: low|medium|high` instead — that is the supported reasoning-level control on 4.7+.
4. Re-run the affected role in isolation against the new model ID to confirm no 400.

## Related
- `opus-4-7-migration.md` — broader behavioral migration (tokenizer inflation, output volume, literal instruction following).
- `model-version-hygiene.md` — the mechanical model-ID swap and `effort:` parameter.

## Source
Anthropic model deprecations / platform release notes — https://platform.claude.com/docs/en/docs/about-claude/model-deprecations (docs.anthropic.com)
