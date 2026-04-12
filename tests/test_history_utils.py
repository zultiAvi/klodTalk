"""Tests for history_utils module."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.history_utils import append_history


class TestAppendHistory:
    def test_creates_history_file(self, temp_workspace):
        append_history(str(temp_workspace), "sess1", "user", "hello")

        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        assert path.is_file()

    def test_appends_valid_jsonl(self, temp_workspace):
        append_history(str(temp_workspace), "sess1", "user", "hello")

        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["role"] == "user"
        assert entry["content"] == "hello"
        assert entry["session_id"] == "sess1"
        assert "timestamp" in entry

    def test_append_multiple(self, temp_workspace):
        append_history(str(temp_workspace), "sess1", "user", "msg1")
        append_history(str(temp_workspace), "sess1", "assistant", "msg2")

        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_creates_dirs(self, tmp_path):
        workspace = tmp_path / "new"
        workspace.mkdir()
        append_history(str(workspace), "s1", "user", "test")

        path = workspace / ".klodTalk" / "history" / "session.jsonl"
        assert path.is_file()

    def test_unicode_content(self, temp_workspace):
        append_history(str(temp_workspace), "s1", "user", "\u05e9\u05dc\u05d5\u05dd")

        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        entry = json.loads(path.read_text().strip())
        assert entry["content"] == "\u05e9\u05dc\u05d5\u05dd"

    def test_empty_content(self, temp_workspace):
        append_history(str(temp_workspace), "s1", "user", "")

        path = temp_workspace / ".klodTalk" / "history" / "session.jsonl"
        entry = json.loads(path.read_text().strip())
        assert entry["content"] == ""
