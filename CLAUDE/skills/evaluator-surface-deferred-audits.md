---
skill_name: evaluator-surface-deferred-audits
triggers:
  - Running the nightly scout idea_evaluator and a finding re-surfaces a CLI/SDK version bump
  - An existing skill's notes contain a "provisional / pending the next X" or "re-run at next floor bump" sentinel
  - Picking top-N ideas and most findings are already-done dupes
summary: "The inverse of the dedupe gate: a finding that is 'already done' may still unlock a DEFERRED audit a skill parked behind a trigger ('re-run at next floor bump', 'provisional pending next bump'). Once that trigger condition is met, EXECUTING the parked audit is a legitimate net-new top pick."
---

# Skill: Evaluator — Surface Deferred Audits That Are Now Due

## When to Use
During the nightly idea_evaluator pass, especially on nights when most scout findings are
already-shipped dupes (a CLI floor that's already pinned, a feature already skilled). Before
concluding "nothing net-new tonight," check whether any existing skill parked work behind a
trigger that the dupe finding has now satisfied.

## Why This Matters
`scout-evaluator-dedupe-existing-work.md` correctly rejects re-implementing done work. But a
"done" finding (e.g. "CLI is at v2.1.195") can be the exact event that makes a previously
DEFERRED audit due. KlodTalk skills routinely defer work with sentinels like
`native-subagent-prompt-drift.md`'s "Re-run this audit at the next floor bump" and four
"provisional" classifications "pending full diff at next floor bump." If the floor has since
moved, executing that parked audit is net-new, low-risk, high-value work — not a dupe.

## Instructions
1. `grep -rniE "provisional|pending (the )?next|re-run .* at .* (floor|bump)|defer" CLAUDE/skills/`
   to list parked/deferred work and its trigger condition.
2. For each hit, check whether the trigger has fired (e.g. compare the skill's last-confirmed
   version against the current pinned CLI floor in `required-minimum-version-pin.md`, or against
   tonight's website_scout changelog finding).
3. If fired → recommend EXECUTING the parked audit as a top candidate. Scope = update that
   skill's notes (and only make surgical role edits if a real conflict is found). Cite the
   triggering finding and the sentinel line.
4. If not yet fired → leave it; note in Deferred Ideas only if relevant.

## Related
- `scout-evaluator-dedupe-existing-work.md` — the complementary gate (reject already-done).
- `native-subagent-prompt-drift.md` — canonical example of a skill that parks an audit behind a
  floor-bump trigger.
- `required-minimum-version-pin.md` — the pinned floor that most version-gated audits key off.
