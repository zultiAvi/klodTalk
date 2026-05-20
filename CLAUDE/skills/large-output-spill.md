---
skill_name: large-output-spill
triggers:
  - A pipeline role is about to write a large `out_message.txt` (codegen dump, full test log, large analysis)
  - Downstream role context budget is tight and re-reading the full output would blow the window
  - Coder/QA/Reviewer handoffs producing more than ~8K tokens of text
summary: "Spill large role outputs to a sidecar file under `.klodTalk/team/current/spill_<role>_<ts>.txt` and write only a one-line reference into `out_message.txt` to keep the next role's context bounded."
---

# Skill: Large-Output Spill Pattern for `out_message.txt`

## Quick Reference
- Threshold heuristic: spill when output exceeds ~8,000 tokens (~32K bytes / ~600 lines).
- Sidecar path: `.klodTalk/team/current/spill_<role>_<UTC-timestamp>.txt`.
- Reference line written into `out_message.txt`:
  `[SPILLED: .klodTalk/team/current/spill_<role>_<ts>.txt -- <N> lines]`.
- Spill files are ephemeral -- never commit them (gitignored under `.klodTalk/`).

## When to Use
KlodTalk pipelines pass role outputs file-to-file via `out_message.txt`. When the producing role emits a very large payload (full codegen, raw test logs, big analysis dumps), the next role's context window can fill silently -- causing truncated handoffs or degraded reasoning. Use this skill any time a role's output would exceed roughly 8K tokens. Pairs with `pipeline-handoff.md`: handoff.md carries the structured summary; the spill file carries the bulk artefact the next role can pull selectively.

## Instructions

### Producer side (the role finishing its stage)
1. Write the full output to a temp file first (e.g. `/tmp/out.full`).
2. Check size:
   ```bash
   lines=$(wc -l < /tmp/out.full)
   bytes=$(wc -c < /tmp/out.full)
   ```
3. If `bytes > 32000` (or `lines > 600`), spill:
   ```bash
   ts=$(date -u +%Y%m%dT%H%M%SZ)
   spill=".klodTalk/team/current/spill_${ROLE}_${ts}.txt"
   mv /tmp/out.full "$spill"
   printf '[SPILLED: %s -- %s lines]\n' "$spill" "$lines" > out_message.txt
   ```
4. Otherwise, just `mv /tmp/out.full out_message.txt`.
5. Optionally include a short (~10-line) head preview in `out_message.txt` above the `[SPILLED: ...]` reference so the next role gets a flavour without opening the file.

### Consumer side (the next role)
1. Read `out_message.txt` first.
2. If it matches the regex `^\[SPILLED: (.+) -- \d+ lines\]$` on a line, open the referenced path.
3. Read only the sections you need (head/tail/grep) -- do not blindly dump the whole file into your reasoning context.
4. If the spill file is missing, treat it as a stage failure (see `pipeline-stage-isolation.md`).

### Gitignore guidance
`.klodTalk/` is already gitignored. Spill files therefore stay local to the run by design. Do NOT add explicit `git add` lines for spill files in any role's commit step.

### Threshold rationale
The 8K-token / 32KB heuristic is intentionally conservative: it leaves room for the next role's prompt, accumulated BTW messages, and reviewer feedback within a 200K context window across a 4-5 stage pipeline.

## Related
- `pipeline-handoff.md` -- the structured-summary companion to this bulk-artefact pattern.
- `pipeline-stage-isolation.md` -- how to handle a missing spill file as a stage failure.
- `selective-git-staging-nightly.md` -- reminder that `.klodTalk/` artefacts must not be staged.

## Source
Managed Agents -- Large Output Spill to File -- https://platform.claude.com/docs/en/managed-agents/overview (docs.anthropic.com, 2026-05-19).
