"""Tests for HistoryStore."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from history_store import HistoryStore


class TestHistoryStore:
    def test_append_creates_file(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "hello world")

        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        assert path.is_file()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["role"] == "user"
        assert entry["content"] == "hello world"
        assert entry["session_id"] == "sess1"

    def test_append_multiple_messages(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "first")
        store.append("sess1", str(temp_workspace), "assistant", "second")

        msgs = store.read_session("sess1", str(temp_workspace))
        assert len(msgs) == 2
        assert msgs[0]["content"] == "first"
        assert msgs[1]["content"] == "second"

    def test_read_nonexistent_returns_empty(self, temp_workspace):
        store = HistoryStore()
        msgs = store.read_session("none", str(temp_workspace))
        assert msgs == []

    def test_read_with_model(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "assistant", "reply", model="opus")

        msgs = store.read_session("sess1", str(temp_workspace))
        assert msgs[0]["model"] == "opus"

    def test_append_empty_content(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "")

        msgs = store.read_session("sess1", str(temp_workspace))
        assert len(msgs) == 1
        assert msgs[0]["content"] == ""

    def test_append_unicode_content(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd")

        msgs = store.read_session("sess1", str(temp_workspace))
        assert msgs[0]["content"] == "\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd"

    def test_append_multiline_content(self, temp_workspace):
        store = HistoryStore()
        content = "line1\nline2\nline3"
        store.append("sess1", str(temp_workspace), "user", content)

        msgs = store.read_session("sess1", str(temp_workspace))
        assert msgs[0]["content"] == content

    def test_append_content_with_json_chars(self, temp_workspace):
        store = HistoryStore()
        content = '{"key": "value", "list": [1, 2, 3]}'
        store.append("sess1", str(temp_workspace), "user", content)

        msgs = store.read_session("sess1", str(temp_workspace))
        assert msgs[0]["content"] == content

    def test_timestamp_present(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "test")

        msgs = store.read_session("sess1", str(temp_workspace))
        assert "timestamp" in msgs[0]
        assert msgs[0]["timestamp"].endswith("Z")

    def test_model_omitted_when_empty(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "test")

        msgs = store.read_session("sess1", str(temp_workspace))
        assert "model" not in msgs[0]

    def test_multiple_sessions_in_same_file(self, temp_workspace):
        store = HistoryStore()
        store.append("sess1", str(temp_workspace), "user", "msg1")
        store.append("sess2", str(temp_workspace), "user", "msg2")
        store.append("sess1", str(temp_workspace), "assistant", "reply1")

        # read_session returns ALL messages (no session filtering in current impl)
        msgs = store.read_session("sess1", str(temp_workspace))
        assert len(msgs) == 3

    def test_read_skips_blank_lines(self, temp_workspace):
        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        entry = json.dumps({"session_id": "s1", "role": "user", "content": "test", "timestamp": "2024-01-01T00:00:00Z"})
        path.write_text(entry + "\n\n\n" + entry + "\n")

        store = HistoryStore()
        msgs = store.read_session("s1", str(temp_workspace))
        assert len(msgs) == 2

    def test_read_skips_corrupt_lines(self, temp_workspace):
        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        good = json.dumps({"session_id": "s1", "role": "user", "content": "ok", "timestamp": "2024-01-01T00:00:00Z"})
        path.write_text(good + "\nNOT_JSON\n" + good + "\n")

        store = HistoryStore()
        msgs = store.read_session("s1", str(temp_workspace))
        assert len(msgs) == 2

    def test_creates_history_dir_if_missing(self, tmp_path):
        workspace = tmp_path / "new_workspace"
        workspace.mkdir()

        store = HistoryStore()
        store.append("sess1", str(workspace), "user", "test")

        path = workspace / ".klodTalk" / "history" / "session.jsonl"
        assert path.is_file()

    def test_large_content(self, temp_workspace):
        store = HistoryStore()
        large = "x" * 100_000
        store.append("sess1", str(temp_workspace), "user", large)

        msgs = store.read_session("sess1", str(temp_workspace))
        assert len(msgs[0]["content"]) == 100_000
