# Team: Memory Curator

Standalone post-pipeline memory-curation team. Reads completed-session artifacts (`hook_events.jsonl`, `coder_output.txt`, `handoff.md`, `reviewer_output.txt`, `evaluated_ideas.md`) plus recent git log, and proposes additions to `.klodTalk/instincts.md` and `CLAUDE/skills/`. Writes Markdown only -- no executable code changes.

Single-member pipeline, no review loop. The role is reasoning-heavy (pattern extraction from heterogeneous logs) so it runs on `sonnet`.

## disabled

(Toggle this to `## enabled` to activate. Default is disabled so the team does not appear in default listings or get scheduled until first explicit activation.)

## Members

| Name | Role | Model | Optional |
|------|------|-------|----------|
| memory_curator | memory_curator | sonnet | |

## Pipeline

1. **memory_curator** -- Read `.klodTalk/team/current/hook_events.jsonl`, `coder_output.txt`, `handoff.md`, `reviewer_output.txt`, `evaluated_ideas.md` (whichever exist) and recent git log. Compare against existing `.klodTalk/instincts.md` and `CLAUDE/skills/*.md` for duplicates. Write `memory_curation_report.md` with proposed instincts and skills; optionally append to `instincts.md` and create new skill files when proposals are unambiguous and non-duplicate. Commit Markdown changes with message `memory-curator: <summary>`.

## Source

`affaan-m/everything-claude-code` -- https://github.com/affaan-m/everything-claude-code (continuous-learning skill, pattern extraction into reusable instincts). Cross-reinforced by Anthropic Managed Agents "dreaming" autonomous between-session memory curation.
