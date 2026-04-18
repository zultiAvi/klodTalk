"""Tests for JSONL reader module."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from jsonl_reader import (
    is_noise,
    get_content_text,
    estimate_tokens,
    enrich_event,
    read_session_jsonl,
    discover_archived_sessions,
    read_subagent_jsonl,
    aggregate_session_tokens,
)


class TestIsNoise:
    def test_permission_mode_is_noise(self):
        assert is_noise({"type": "permission-mode"}) is True

    def test_file_history_snapshot_is_noise(self):
        assert is_noise({"type": "file-history-snapshot"}) is True

    def test_queued_command_type_is_noise(self):
        assert is_noise({"type": "queued_command"}) is True

    def test_queued_command_attachment_is_noise(self):
        event = {"type": "human", "attachments": [{"type": "queued_command"}]}
        assert is_noise(event) is True

    def test_queue_operation_remove_is_noise(self):
        assert is_noise({"type": "queue-operation", "operation": "remove"}) is True

    def test_queue_operation_add_is_not_noise(self):
        assert is_noise({"type": "queue-operation", "operation": "add"}) is False

    def test_task_notification_pattern_is_noise(self):
        event = {"type": "human", "content": "Some <task-notification> text"}
        assert is_noise(event) is True

    def test_command_message_pattern_is_noise(self):
        event = {"type": "human", "content": "Some <command-message> text"}
        assert is_noise(event) is True

    def test_normal_assistant_event_not_noise(self):
        event = {"type": "assistant", "content": "Hello, I can help with that."}
        assert is_noise(event) is False

    def test_normal_human_event_not_noise(self):
        event = {"type": "human", "content": "Please fix this bug."}
        assert is_noise(event) is False

    def test_empty_event_not_noise(self):
        assert is_noise({}) is False


class TestGetContentText:
    def test_string_content(self):
        assert get_content_text("hello") == "hello"

    def test_list_of_strings(self):
        assert get_content_text(["hello", "world"]) == "hello world"

    def test_list_of_text_dicts(self):
        content = [{"type": "text", "text": "hello"}, {"type": "text", "text": "world"}]
        assert get_content_text(content) == "hello world"

    def test_nested_content(self):
        content = [{"type": "wrapper", "content": "inner text"}]
        assert get_content_text(content) == "inner text"

    def test_dict_with_type_text(self):
        assert get_content_text({"type": "text", "text": "hi"}) == "hi"

    def test_dict_with_content_key(self):
        assert get_content_text({"content": "nested"}) == "nested"

    def test_empty_content(self):
        assert get_content_text("") == ""
        assert get_content_text([]) == ""
        assert get_content_text({}) == ""

    def test_none_like_content(self):
        assert get_content_text(42) == ""


class TestEstimateTokens:
    def test_basic_estimate(self):
        assert estimate_tokens("abcdefgh") == 2

    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_short_string(self):
        assert estimate_tokens("ab") == 0


class TestEnrichEvent:
    def test_human_role_type(self):
        result = enrich_event({"type": "human"})
        assert result["role_type"] == "user"

    def test_assistant_role_type(self):
        result = enrich_event({"type": "assistant"})
        assert result["role_type"] == "assistant"

    def test_tool_use_role_type(self):
        result = enrich_event({"type": "tool_use"})
        assert result["role_type"] == "tool"

    def test_tool_result_role_type(self):
        result = enrich_event({"type": "tool_result"})
        assert result["role_type"] == "tool"

    def test_system_role_type(self):
        result = enrich_event({"type": "system"})
        assert result["role_type"] == "system"

    def test_hook_role_type(self):
        result = enrich_event({"type": "hook_success"})
        assert result["role_type"] == "hook"

    def test_unknown_role_type(self):
        result = enrich_event({"type": "custom_thing"})
        assert result["role_type"] == "custom_thing"

    def test_empty_type_role(self):
        result = enrich_event({})
        assert result["role_type"] == "unknown"

    def test_tokens_from_usage(self):
        event = {
            "type": "assistant",
            "message": {
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_creation_input_tokens": 10,
                    "cache_read_input_tokens": 5,
                }
            }
        }
        result = enrich_event(event)
        assert result["tokens"]["input"] == 100
        assert result["tokens"]["output"] == 50
        assert result["tokens"]["cache_creation"] == 10
        assert result["tokens"]["cache_read"] == 5

    def test_tokens_default_zero(self):
        result = enrich_event({"type": "human"})
        assert result["tokens"]["input"] == 0
        assert result["tokens"]["output"] == 0

    def test_compaction_boundary(self):
        event = {
            "type": "system",
            "subtype": "compact_boundary",
            "content": "Conversation compacted due to length."
        }
        result = enrich_event(event)
        assert result["is_compaction_boundary"] is True

    def test_not_compaction_boundary(self):
        event = {"type": "system", "content": "Something else"}
        result = enrich_event(event)
        assert result["is_compaction_boundary"] is False

    def test_subagent_id_from_tool_result(self):
        event = {"type": "tool_result", "toolUseResult": {"agentId": "abc123"}}
        result = enrich_event(event)
        assert result["subagent_id"] == "abc123"

    def test_subagent_id_from_content(self):
        event = {"type": "assistant", "content": "agentId: deadbeef running"}
        result = enrich_event(event)
        assert result["subagent_id"] == "deadbeef"

    def test_no_subagent_id(self):
        result = enrich_event({"type": "assistant", "content": "just text"})
        assert result["subagent_id"] == ""

    def test_original_event_not_modified(self):
        event = {"type": "human", "content": "test"}
        enrich_event(event)
        assert "role_type" not in event


class TestReadSessionJsonl:
    def test_read_valid_jsonl(self, tmp_path):
        path = tmp_path / "session.jsonl"
        events = [
            {"type": "human", "content": "Hello"},
            {"type": "assistant", "content": "Hi there"},
        ]
        path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        result = read_session_jsonl(str(path))
        assert len(result) == 2
        assert result[0]["role_type"] == "user"
        assert result[1]["role_type"] == "assistant"

    def test_filters_noise(self, tmp_path):
        path = tmp_path / "session.jsonl"
        events = [
            {"type": "human", "content": "Hello"},
            {"type": "permission-mode"},
            {"type": "assistant", "content": "Hi"},
        ]
        path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        result = read_session_jsonl(str(path), filter_noise=True)
        assert len(result) == 2

    def test_no_filter_noise(self, tmp_path):
        path = tmp_path / "session.jsonl"
        events = [
            {"type": "human", "content": "Hello"},
            {"type": "permission-mode"},
        ]
        path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
        result = read_session_jsonl(str(path), filter_noise=False)
        assert len(result) == 2

    def test_skips_invalid_json(self, tmp_path):
        path = tmp_path / "session.jsonl"
        path.write_text('{"type":"human","content":"ok"}\nNOT JSON\n{"type":"assistant","content":"yes"}\n')
        result = read_session_jsonl(str(path))
        assert len(result) == 2

    def test_nonexistent_file(self):
        result = read_session_jsonl("/nonexistent/path.jsonl")
        assert result == []

    def test_empty_file(self, tmp_path):
        path = tmp_path / "session.jsonl"
        path.write_text("")
        result = read_session_jsonl(str(path))
        assert result == []

    def test_blank_lines_skipped(self, tmp_path):
        path = tmp_path / "session.jsonl"
        path.write_text('\n\n{"type":"human","content":"hi"}\n\n')
        result = read_session_jsonl(str(path))
        assert len(result) == 1


class TestDiscoverArchivedSessions:
    def test_discovers_sessions(self, tmp_path):
        # Create structure: <hash>/<session_id>.jsonl
        hash_dir = tmp_path / "abc123hash"
        hash_dir.mkdir()
        jsonl = hash_dir / "session_001.jsonl"
        jsonl.write_text('{"type":"human","content":"hi"}\n')

        result = discover_archived_sessions(str(tmp_path))
        assert len(result) == 1
        assert result[0]["session_id"] == "session_001"
        assert result[0]["size_bytes"] > 0
        assert result[0]["subagent_ids"] == []

    def test_discovers_subagents(self, tmp_path):
        hash_dir = tmp_path / "abc123"
        hash_dir.mkdir()
        jsonl = hash_dir / "sess01.jsonl"
        jsonl.write_text('{"type":"human"}\n')

        sa_dir = hash_dir / "sess01" / "subagents"
        sa_dir.mkdir(parents=True)
        (sa_dir / "agent-deadbeef.jsonl").write_text('{"type":"assistant"}\n')
        (sa_dir / "agent-cafe1234.jsonl").write_text('{"type":"assistant"}\n')

        result = discover_archived_sessions(str(tmp_path))
        assert len(result) == 1
        assert sorted(result[0]["subagent_ids"]) == ["cafe1234", "deadbeef"]

    def test_empty_directory(self, tmp_path):
        result = discover_archived_sessions(str(tmp_path))
        assert result == []

    def test_nonexistent_directory(self):
        result = discover_archived_sessions("/nonexistent")
        assert result == []


class TestReadSubagentJsonl:
    def test_reads_subagent(self, tmp_path):
        hash_dir = tmp_path / "hashdir"
        hash_dir.mkdir()
        (hash_dir / "parent_sess.jsonl").write_text('{"type":"human"}\n')

        sa_dir = hash_dir / "parent_sess" / "subagents"
        sa_dir.mkdir(parents=True)
        (sa_dir / "agent-abc123.jsonl").write_text('{"type":"assistant","content":"sub output"}\n')

        result = read_subagent_jsonl(str(tmp_path), "parent_sess", "abc123")
        assert len(result) == 1
        assert result[0]["role_type"] == "assistant"

    def test_missing_subagent(self, tmp_path):
        hash_dir = tmp_path / "hashdir"
        hash_dir.mkdir()
        (hash_dir / "parent_sess.jsonl").write_text('{"type":"human"}\n')

        result = read_subagent_jsonl(str(tmp_path), "parent_sess", "nonexistent")
        assert result == []


class TestAggregateSessionTokens:
    def test_aggregates_tokens(self):
        events = [
            {"tokens": {"input": 100, "output": 50, "cache_creation": 10, "cache_read": 5}},
            {"tokens": {"input": 200, "output": 100, "cache_creation": 20, "cache_read": 10}},
        ]
        totals = aggregate_session_tokens(events)
        assert totals["input"] == 300
        assert totals["output"] == 150
        assert totals["cache_creation"] == 30
        assert totals["cache_read"] == 15

    def test_empty_events(self):
        totals = aggregate_session_tokens([])
        assert totals == {"input": 0, "output": 0, "cache_creation": 0, "cache_read": 0}

    def test_missing_token_fields(self):
        events = [{"tokens": {"input": 10}}, {}]
        totals = aggregate_session_tokens(events)
        assert totals["input"] == 10
        assert totals["output"] == 0
