---
skill_name: verify-env-var-names-against-changelog
triggers:
  - A nightly website_scout finding restates a Claude Code env var / CLI flag name that an existing KlodTalk skill or instinct already documents
  - Reconfirming a prior run's CLI fact and the exact env-var/flag spelling matters (mitigation knob, feature toggle)
  - Auditing skills/instincts that cite CLAUDE_* env vars or CLI flags for accuracy
summary: "Env-var/flag NAMES baked into existing KlodTalk skills/instincts by a prior nightly can be hallucinations, not just new scout claims. Instinct #44 (verify new claims vs raw CHANGELOG) also applies retroactively: when a run reconfirms a CLI fact, re-verify the exact spelling of any env var/flag already committed. A mismatch is a top-value CORRECTION finding, not a dedupe-out. Real case (2026-07-01): the watchdog disable knob was committed as CLAUDE_CODE_DISABLE_IDLE_WATCHDOG (0 hits in raw CHANGELOG); the real var is CLAUDE_ENABLE_STREAM_WATCHDOG=0."
---

# Skill: Re-verify Committed Env-Var / Flag Names Against the Raw CHANGELOG

## When to Use
A website_scout finding touches a Claude Code env var or CLI flag that an existing
skill/instinct already documents, OR you are reconfirming a prior nightly's CLI fact
where the exact spelling of a knob is load-bearing (a mitigation the operator will paste
into container env). This extends instinct #44 from *new* scout claims to *already-landed*
artifacts.

## Why This Matters
A hallucinated env-var name is worse than a missing one: an operator following the skill
sets a no-op var, gets zero mitigation, and concludes the feature "can't be disabled".
Prior nightlies invent plausible-looking `CLAUDE_CODE_*` names. Once committed to a skill
AND an instinct, the wrong name self-reinforces across runs (the next scout "confirms" it
against KlodTalk's own docs, not the source).

## Instructions
1. Fetch the RAW changelog (never a web summary):
   `curl -s https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`.
2. `grep -niE '<VAR_OR_FLAG>' cc_changelog.md`. **Zero hits = hallucinated** — do not trust
   the committed spelling. Search the concept (e.g. `watchdog`, `sandbox`) to find the real
   name; note the CLI has multiple related knobs (enable vs disable, `_MS` threshold vars).
3. When a mismatch is found, correct ALL copies in lockstep: the owning skill (body +
   `summary:` frontmatter), the matching instinct in `.klodTalk/instincts.md`, and any
   `required-minimum-version-pin.md` history row citing it. Grep to confirm zero residual
   occurrences of the wrong name after editing.
4. Do NOT assert a numeric DEFAULT for a threshold var unless the raw CHANGELOG states it
   for the current version — older entries may cite a different default than the current
   default-on behavior (the watchdog window is a live example: 90s in an old entry vs the
   5-minute default-on figure in v2.1.196). State "set it explicitly" instead of guessing.
5. Feed the correction to the evaluator as a top candidate — a wrong-name fix is high
   impact / low effort, the inverse of a dedupe-out (see `evaluator-surface-deferred-audits.md`).

## Cross-References
- `.klodTalk/instincts.md` #44 (verify CLI claims vs raw CHANGELOG) — this skill applies it retroactively.
- `idle-watchdog-long-session.md` — the corrected watchdog knob (`CLAUDE_ENABLE_STREAM_WATCHDOG=0`).
- `evaluator-surface-deferred-audits.md` — already-committed facts can still become top findings.
