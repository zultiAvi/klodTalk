---
skill_name: refusal-stop-details-classification
triggers:
  - A sub-agent or single-agent run returns no output and you suspect a refusal
  - Diagnosing KlodTalk's recurring "agent refused authorized code work" failure
  - Inspecting Claude `--output-format json` payloads for stop_reason / stop_details
summary: "Classify a Claude run's stop_reason/stop_details: stop_reason=='refusal' with a null category is the signature of a hallucinated / workspace-auth false-positive refusal (re-assert the auth preamble); a cyber/bio/reasoning_extraction category is a genuine policy refusal to surface verbatim."
---

# Skill: Refusal stop_details Classification

## Quick Reference
- Helper: `server/run_agent.py:classify_refusal(data) -> (is_refusal: bool, category: str|None, explanation: str)`
- Logger: `server/run_agent.py:log_refusal(data, source)` — stderr WARNING + `team/current/refusal_events.log`; observational only, NO auto-retry.
- Call sites: single-agent (`result.stdout`) and team-orchestrator (`claude_orchestrator_output.json`) result handling in `run_execute_mode`.
- Heuristic: `stop_reason == "refusal"` AND `category is None` -> likely workspace-auth false-positive; re-assert the authorization preamble.
- `category in {"cyber","bio","reasoning_extraction"}` (`GENUINE_REFUSAL_CATEGORIES`) -> genuine policy refusal; surface `explanation` verbatim.

## When to Use
- A run produced empty/short output and you need to tell a real policy refusal apart from KlodTalk's recurring hallucinated refusal.
- Extending refusal handling (e.g. someday adding a re-assert-and-retry loop). Keep the current change observational unless explicitly approved.

## Background
As of the Claude Platform API change on **2026-06-02**, a run returning
`stop_reason: "refusal"` with no output is **not billed**, and `stop_details`
is documented as `{category, explanation}` where `category` is one of
`"cyber"`, `"bio"`, `"reasoning_extraction"`, or `null`:

| stop_reason | category | Meaning | Action |
|-------------|----------|---------|--------|
| `refusal`   | `null`   | Hallucinated / workspace-auth false positive (KlodTalk's most recurring failure) | WARNING: re-assert the authorization preamble |
| `refusal`   | `cyber`  | Genuine policy refusal (offensive-security content) | Surface `explanation` verbatim |
| `refusal`   | `bio`    | Genuine policy refusal (bio content) | Surface `explanation` verbatim |
| `refusal`   | `reasoning_extraction` | Genuine policy refusal — Fable 5 blocks reverse-engineering / duplication of model outputs | Surface `explanation` verbatim |
| anything else | n/a    | Not a refusal | none |

`stop_details` may be **missing or None** on older CLIs or non-refusal runs —
`classify_refusal` treats those defensively as `(is_refusal, None, "")`.

Note: Fable 5 (2026-06-09) added a third genuine category
`reasoning_extraction`; treat it as a genuine policy refusal identical to
cyber/bio. `log_refusal` keys off `GENUINE_REFUSAL_CATEGORIES` (the frozenset
of all genuine categories), so a null OR otherwise-unrecognized category falls
to the workspace-auth-false-positive branch.

## Implementation Notes
- `parse_claude_json_output()` already does `json.loads` for the usage summary; its
  two-value signature is unchanged (other callers depend on it). `classify_refusal`
  is a SEPARATE additive helper; the call sites parse the raw JSON once and pass the
  dict to both, avoiding a second `json.loads`.
- The logger writes the same WARNING to stderr (the server mirrors run_agent stderr
  into the session log via `session_log.append_raw`, see `server.py:~691`) and appends
  a timestamped line to `team/current/refusal_events.log` for durability.
- Constants: `STOP_REASON_REFUSAL`, `REFUSAL_CATEGORY_CYBER`, `REFUSAL_CATEGORY_BIO`,
  `REFUSAL_CATEGORY_REASONING_EXTRACTION`, and the `GENUINE_REFUSAL_CATEGORIES`
  frozenset that `log_refusal` checks membership against.

## Cross-References
- `workspace-authorization-preamble.md` — the preamble to re-assert when a
  null-category refusal fires on authorized workspace code.
- `feedback_orchestrator_hallucinated_refusal.md` (auto-memory) — the failure mode
  this detection targets.

## Source
- Claude Platform API release notes (2026-06-02 / 2026-05-28 / 2026-06-09) —
  https://platform.claude.com/docs/en/release-notes/api
  (the 2026-06-09 release added the `reasoning_extraction` category with Fable 5).
