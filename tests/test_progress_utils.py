"""Tests for progress_utils module."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from utils.progress_utils import write_progress, progress_set


class TestWriteProgress:
    def test_write_creates_file(self, temp_workspace):
        write_progress("Starting...", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.is_file()
        assert path.read_text() == "Starting..."

    def test_write_overwrites(self, temp_workspace):
        write_progress("first", str(temp_workspace))
        write_progress("second", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.read_text() == "second"

    def test_write_empty(self, temp_workspace):
        write_progress("", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.read_text() == ""

    def test_write_creates_dirs(self, tmp_path):
        workspace = tmp_path / "new"
        workspace.mkdir()
        write_progress("test", str(workspace))
        path = workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.is_file()


class TestProgressSet:
    def test_format(self, temp_workspace):
        progress_set(1, 5, "Building", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.read_text() == "[1/5] Building"

    def test_progress_at_start(self, temp_workspace):
        progress_set(0, 10, "Starting", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.read_text() == "[0/10] Starting"

    def test_progress_at_end(self, temp_workspace):
        progress_set(10, 10, "Done", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert path.read_text() == "[10/10] Done"

    def test_progress_with_special_chars(self, temp_workspace):
        progress_set(1, 3, "Running tests...", str(temp_workspace))
        path = temp_workspace / ".klodTalk" / "out_messages" / "progress_message.txt"
        assert "Running tests..." in path.read_text()
