---
skill_name: otel-assistant-response-event
triggers:
  - Capturing the model's response text for session/observability logging
  - Wiring OpenTelemetry log events into KlodTalk's observability surface
  - Deciding between hook-event JSONL (tool/subagent lifecycle) and OTEL (response text)
summary: "`claude_code.assistant_response` (CLI 2.1.193) is an OpenTelemetry log event carrying the model's response text; complements KlodTalk's JSONL hook pipeline (which logs tool/subagent lifecycle, not response text). Opt-in and privacy-sensitive — keep it routed to the run-results folder."
description: "Documents the claude_code.assistant_response OpenTelemetry log event added in Claude Code CLI 2.1.193, which carries the model's response text. Use when adding response-text capture to KlodTalk's observability surface, when contrasting the OTEL log-event channel against the existing JSONL hook-event pipeline, or when handling the privacy/volume tradeoffs of logging assistant output. Note response content is redacted unless OTEL_LOG_ASSISTANT_RESPONSES=1."
---

# Skill: claude_code.assistant_response OTEL Log Event

## Quick Reference
- Event name: `claude_code.assistant_response` (OpenTelemetry **log event**)
- Carries: the model's response text
- Available since: Claude Code **v2.1.193** (floor pinned — see `required-minimum-version-pin.md`)
- Gating: response content is **redacted unless `OTEL_LOG_ASSISTANT_RESPONSES=1`**. When that var is unset it follows `OTEL_LOG_USER_PROMPTS`, so a deployment already logging prompt content starts receiving response content on upgrade — set `OTEL_LOG_ASSISTANT_RESPONSES=0` to keep prompts-only.
- Channel: OTEL log events — distinct from KlodTalk's JSONL hook pipeline.

## Position vs KlodTalk's Hook Pipeline
KlodTalk's existing observability is JSONL hook events: tool/subagent **lifecycle** only.
- `post_tool_use_logger.sh` → tool calls (`hook-event-logging.md`, `multi-agent-hook-observability.md`)
- `subagent_lifecycle_logger.sh` → SubagentStart/Stop
- single-write append discipline → `broadcast-log-event-single-write.md`

None of those capture the model's **response text** — today that flows only through `out_message.txt` / MessageDisplay. `claude_code.assistant_response` is the harness-native channel for response text, so it complements (does not replace) the hook JSONL.

## CAVEAT — verify the OTEL transport env vars
The redaction toggle (`OTEL_LOG_ASSISTANT_RESPONSES`) is confirmed from the v2.1.193 changelog. The broader telemetry-enable / exporter-endpoint env vars are NOT asserted here — **verify the exact OTEL enable/transport env vars against the changelog/docs before relying on them**; do not fabricate names.

## Privacy / Volume
Response text can be large and sensitive. Keep it **opt-in** and route the exporter sink to the per-run results folder (per the run-results-folder debug-viz instinct) rather than a shared/persistent sink. Leave `OTEL_LOG_ASSISTANT_RESPONSES` unset/`0` by default.

## Cross-References
- `multi-agent-hook-observability.md` — the JSONL lifecycle pipeline this event complements.
- `hook-event-logging.md` — hook exit-0 discipline and the JSONL field reference.
- `broadcast-log-event-single-write.md` — single-write append discipline for shared logs.
- `required-minimum-version-pin.md` — the 2.1.193 floor this event requires.

## Source
- Claude Code CHANGELOG v2.1.193 — https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md (github.com/anthropics/claude-code, official, 82,000+ stars).
