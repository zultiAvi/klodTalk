"""Tests for UnreadState."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

import unread_state as us_module
from unread_state import UnreadState


class TestUnreadState:
    def test_mark_unread_and_get(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", ["alice", "bob"])

        assert "sess1" in state.get_unread("alice")
        assert "sess1" in state.get_unread("bob")
        assert state.get_unread("charlie") == []

    def test_mark_read(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", ["alice"])
        state.mark_unread("sess2", ["alice"])
        state.mark_read("sess1", "alice")

        unread = state.get_unread("alice")
        assert "sess1" not in unread
        assert "sess2" in unread

    def test_no_duplicates(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", ["alice"])
        state.mark_unread("sess1", ["alice"])

        assert state.get_unread("alice").count("sess1") == 1

    def test_mark_read_nonexistent_user(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        # Should not raise
        state.mark_read("sess1", "nobody")
        assert state.get_unread("nobody") == []

    def test_mark_read_nonexistent_session(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", ["alice"])
        state.mark_read("sess_nonexistent", "alice")

        # sess1 should still be unread
        assert "sess1" in state.get_unread("alice")

    def test_empty_users_list(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", [])
        # No users added
        assert state.get_unread("alice") == []

    def test_multiple_sessions_per_user(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        for i in range(10):
            state.mark_unread(f"sess{i}", ["alice"])

        unread = state.get_unread("alice")
        assert len(unread) == 10
        for i in range(10):
            assert f"sess{i}" in unread

    def test_mark_read_all_sessions(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", ["alice"])
        state.mark_unread("sess2", ["alice"])
        state.mark_read("sess1", "alice")
        state.mark_read("sess2", "alice")

        assert state.get_unread("alice") == []

    def test_persistence_save_and_load(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state1 = UnreadState()
        state1.mark_unread("sess1", ["alice", "bob"])

        # Create a new instance that should load from disk
        state2 = UnreadState()
        assert "sess1" in state2.get_unread("alice")
        assert "sess1" in state2.get_unread("bob")

    def test_get_unread_returns_copy(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        state.mark_unread("sess1", ["alice"])

        unread = state.get_unread("alice")
        unread.append("fake_session")

        # Internal state should not be modified
        assert "fake_session" not in state.get_unread("alice")

    def test_corrupt_file_recovery(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        with open(path, "w") as f:
            f.write("CORRUPT DATA")

        state = UnreadState()
        assert state.get_unread("alice") == []

    def test_many_users(self, tmp_path, monkeypatch):
        path = str(tmp_path / "unread_state.json")
        monkeypatch.setattr(us_module, "UNREAD_STATE_PATH", path)

        state = UnreadState()
        users = [f"user_{i}" for i in range(100)]
        state.mark_unread("sess1", users)

        for user in users:
            assert "sess1" in state.get_unread(user)
