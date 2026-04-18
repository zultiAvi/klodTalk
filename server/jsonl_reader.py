"""Read and enrich Claude Code CLI JSONL session files."""

import json
import re
from pathlib import Path
from typing import Any


# --- Noise filtering ---

NOISE_TYPES = {"permission-mode", "file-history-snapshot", "queued_command"}
NOISE_PATTERNS = ["<task-notification>", "<command-message>"]


def is_noise(event: dict) -> bool:
    """Return True if the event is non-meaningful noise."""
    etype = event.get("type", "")
    if etype in NOISE_TYPES:
        return True
    # Attachments with type "queued_command"
    for att in event.get("attachments", []):
        if att.get("type") == "queued_command":
            return True
    # Queue operations with operation "remove"
    if etype == "queue-operation" and event.get("operation") == "remove":
        return True
    # Text content containing noise patterns
    text = get_content_text(event.get("content", ""))
    for pattern in NOISE_PATTERNS:
        if pattern in text:
            return True
    return False


# --- Content text extraction ---

def get_content_text(content) -> str:
    """Recursively extract text from nested content structures."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif "content" in item:
                    parts.append(get_content_text(item["content"]))
        return " ".join(parts)
    if isinstance(content, dict):
        if content.get("type") == "text":
            return content.get("text", "")
        if "content" in content:
            return get_content_text(content["content"])
    return ""


# --- Token estimation ---

def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


# --- Event enrichment ---

def enrich_event(event: dict) -> dict:
    """Add computed fields: tokens, role_type, is_compaction_boundary."""
    enriched = dict(event)

    # Role type
    etype = event.get("type", "")
    if etype == "human":
        enriched["role_type"] = "user"
    elif etype == "assistant":
        enriched["role_type"] = "assistant"
    elif etype in ("tool_use", "tool_result"):
        enriched["role_type"] = "tool"
    elif etype == "system":
        enriched["role_type"] = "system"
    elif etype in ("hook_success", "hook_start"):
        enriched["role_type"] = "hook"
    else:
        enriched["role_type"] = etype or "unknown"

    # Tokens from authoritative usage data
    usage = event.get("message", {}).get("usage", {}) if isinstance(event.get("message"), dict) else {}
    enriched["tokens"] = {
        "input": usage.get("input_tokens", 0),
        "output": usage.get("output_tokens", 0),
        "cache_creation": usage.get("cache_creation_input_tokens", 0),
        "cache_read": usage.get("cache_read_input_tokens", 0),
    }

    # Compaction boundary detection
    enriched["is_compaction_boundary"] = (
        etype == "system"
        and event.get("subtype") == "compact_boundary"
        and "Conversation compacted" in get_content_text(event.get("content", ""))
    )

    # Sub-agent ID detection
    tool_result = event.get("toolUseResult", {}) if isinstance(event.get("toolUseResult"), dict) else {}
    agent_id = tool_result.get("agentId", "")
    if not agent_id:
        text = get_content_text(event.get("content", ""))
        m = re.search(r"agentId:\s*([a-f0-9]+)", text)
        if m:
            agent_id = m.group(1)
    enriched["subagent_id"] = agent_id

    return enriched


# --- Session reading ---

def read_session_jsonl(jsonl_path: str, filter_noise: bool = True) -> list[dict]:
    """Read a JSONL file and return enriched events."""
    events = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if filter_noise and is_noise(event):
                    continue
                events.append(enrich_event(event))
    except Exception:
        pass
    return events


# --- Session discovery in archive ---

def discover_archived_sessions(archive_dir: str) -> list[dict]:
    """Find all JSONL session files in an archived claude_logs directory.

    archive_dir is typically: <project_folder>/.klodTalk/sessions/<session_id>/claude_logs/
    Claude writes to: ~/.claude/projects/<project_hash>/<session_id>.jsonl
    So the structure inside archive_dir mirrors: <project_hash>/<session_id>.jsonl
    """
    sessions = []
    logs_path = Path(archive_dir)
    if not logs_path.is_dir():
        return sessions
    for jsonl_file in logs_path.glob("*/*.jsonl"):
        session_id = jsonl_file.stem
        # Check for subagent directory
        subagent_dir = jsonl_file.parent / session_id / "subagents"
        subagents = []
        if subagent_dir.is_dir():
            for sa_file in subagent_dir.glob("agent-*.jsonl"):
                subagents.append(sa_file.stem.replace("agent-", ""))
        sessions.append({
            "session_id": session_id,
            "path": str(jsonl_file),
            "size_bytes": jsonl_file.stat().st_size,
            "subagent_ids": subagents,
        })
    return sessions


def read_subagent_jsonl(archive_dir: str, parent_session_id: str, agent_id: str, filter_noise: bool = True) -> list[dict]:
    """Read a sub-agent's JSONL from the archive."""
    logs_path = Path(archive_dir)
    # Search for matching parent session directory
    for jsonl_file in logs_path.glob(f"*/{parent_session_id}.jsonl"):
        subagent_path = jsonl_file.parent / parent_session_id / "subagents" / f"agent-{agent_id}.jsonl"
        if subagent_path.exists():
            return read_session_jsonl(str(subagent_path), filter_noise)
    return []


def aggregate_session_tokens(events: list[dict]) -> dict:
    """Sum token usage across all events."""
    totals = {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}
    for event in events:
        tokens = event.get("tokens", {})
        for key in totals:
            totals[key] += tokens.get(key, 0)
    return totals
