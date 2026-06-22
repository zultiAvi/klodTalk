---
skill_name: team-fact-store
triggers:
  - An orchestrator resumes a team run after a container restart, BTW injection, or session compaction
  - A pipeline role discovers a durable fact (a decision, a measured value, a blocker) worth carrying across steps
  - You need to reconstruct mission state without re-reading the full session transcript
summary: "Durable append-only JSONL fact store at .klodTalk/team/current/facts.jsonl: roles append one structured fact per line via jq, and the orchestrator tails it on resume to recover mission state without re-reading the session."
---

# Skill: Team Fact Store

## Quick Reference
- File: `/workspace/.klodTalk/team/current/facts.jsonl` — one JSON object per line, **append only, never rewrite**.
- Line shape: `{"timestamp":…,"role":…,"fact":…,"tags":[…]}`.
- Append: `jq -nc … >> facts.jsonl` (each role emits its own facts as it works).
- Recover: `jq -r '.fact' facts.jsonl | tail -20` surfaces the last known state.
- Pure shell + `jq` (already in containers) — no new deps, no `server.py`/`run_agent.py` changes.

## When to Use
Use during any long-running team run that can be interrupted. Currently agents only produce `out_message.txt` and `hook_events.jsonl`; neither is a queryable running ledger of decisions. The fact store is a lightweight recovery surface: roles append facts as they go, and a resumed orchestrator reconstructs state from the tail instead of starting blind.

## Instructions
1. **Append a fact** (any role, at any decision point) — never edit existing lines:
   ```bash
   FACTS=/workspace/.klodTalk/team/current/facts.jsonl
   jq -nc --arg ts "$(date -u +%FT%TZ)" --arg role "coder" \
     --arg fact "Chose append-only JSONL over rewriting out_message.txt" \
     --argjson tags '["decision","fact-store"]' \
     '{timestamp:$ts, role:$role, fact:$fact, tags:$tags}' >> "$FACTS"
   ```
2. **Recovery protocol** — on orchestrator resume, if `facts.jsonl` exists and is non-empty:
   ```bash
   [ -s "$FACTS" ] && jq -r '.fact' "$FACTS" | tail -20
   ```
   Read the tail to rebuild mission state before re-dispatching roles. Append-only means a crash mid-write at worst loses the last line, never the history.

## Cross-References
- `multi-agent-hook-observability.md` — the sibling `hook_events.jsonl` per-tool ledger.
- `teams/orchestrator.md` — "Context Recovery" section references this skill.

## Source Attribution
- `dsifry/metaswarm` (community): https://github.com/dsifry/metaswarm — ~324 stars. Source of the append-only JSONL fact-store + context-recovery-on-resume pattern.
