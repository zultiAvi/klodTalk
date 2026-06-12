---
skill_name: btw-mid-conversation-system-message
triggers:
  - Reviewing or extending KlodTalk's BTW side-channel handling
  - Investigating why a BTW message busts the prompt cache or reads as chit-chat
  - Migrating BTW off the file + `claude -p` shim onto a structured messages array / Agent SDK
summary: "Opus 4.8 supports `role: \"system\"` messages injected mid-`messages`-array (no beta header, cache-preserving); KlodTalk's BTW today lands as `[BTW]`-prefixed user/context text via a `MODE=btw` `claude -p` shim, so this is a documented FUTURE direction, not a current capability."
---

# Skill: BTW as a Mid-Conversation System Message

## Quick Reference
- Capability (Opus 4.8, GA): you can inject a `role: "system"` message AFTER a user turn inside the `messages` array. The change is treated as an *instruction*, not user text, and it preserves prompt-cache hits.
- No beta header required; requires Opus 4.8 (`claude-opus-4-8` — see `model-version-hygiene.md`).
- KlodTalk's BTW path today does NOT use this — it is a file + `claude -p` shim, so BTW lands as ordinary user/context text.
- This skill is OBSERVATIONAL / FUTURE-DIRECTION. Do not change BTW wiring on the strength of it alone.

## How KlodTalk's BTW Flows Today
1. `handle_btw` (`server/server.py:1503`) appends `[BTW] <content>` to history and broadcasts it (`server.py:~1595/1605`).
2. It writes the payload to `in_messages/btw_message.txt` (`server.py:~1610`).
3. `_run_btw_agent` (`server/server.py:1626`) runs a lightweight `MODE=btw` `claude -p` call (`server.py:~1644`) and the output is logged/broadcast with a `[BTW]` prefix.
- Net effect: BTW is *user/context text* fed through a one-shot `-p` invocation — it is not injected into a running agent's `messages` array, and a long-running agent's prompt cache gets no benefit.

## Cross-Session Relay Loses User Authority (v2.1.166)
As of Claude Code v2.1.166, messages relayed between sessions (e.g. via
`SendMessage`) **lose user-level authority** — they are treated as
non-user-authored — and are **blocked in auto / unattended mode**.
- KlodTalk's BTW is exactly such a cross-session side-channel relay: the payload
  originates in one session and is delivered into another via the file +
  `MODE=btw` `-p` shim, so it arrives as **system / non-user context, not a user
  turn**.
- Implication: any BTW-triggered action that requires *user authority* (e.g.
  approving a gated tool, authorizing a destructive op) will **not be honored in
  unattended nightly runs** — the relayed content is non-user-authored and such
  messages are blocked in auto mode. BTW remains usable as added *context*, but
  do not rely on it to grant permissions in an unattended pipeline.

## When to Use
- Anyone redesigning BTW to inject guidance into an already-running pipeline agent.
- Anyone diagnosing "why does BTW get treated as chit-chat / why did the cache miss".
- Anyone wondering why a BTW that asks for a privileged/gated action is ignored in an unattended run.

## Recommendation (future direction)
- IF/WHEN BTW is migrated off the file + `-p` shim to a structured `messages` array (e.g. an Agent SDK path), route the BTW payload as a mid-conversation `role: "system"` message so it is treated as instruction WITHOUT invalidating the running agent's prompt cache.
- Today's CLI `-p` shim cannot inject a mid-array system message — there is no running `messages` array to splice into. Keep this advisory until a structured-session path exists.

## Cross-References
- `broadcast-message-file-handler.md` — the file plumbing BTW rides on (this skill covers the message *role*, not the plumbing).
- `compaction-api-opt-in.md` — related cache/credit interaction for long sessions.
- `model-version-hygiene.md` — the Opus 4.8 requirement.

## Source
- Mid-conversation system messages (no beta header, Opus 4.8) — https://docs.anthropic.com/en/build-with-claude/mid-conversation-system-messages (platform.claude.com / API release notes, 2026-05-28).
- Cross-session relayed messages lose user authority and are blocked in auto mode — Claude Code CHANGELOG v2.1.166 (https://code.claude.com/docs/en/changelog).
