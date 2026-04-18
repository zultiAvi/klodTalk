"""Tests for TokenStore."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

import token_store as ts_module
from token_store import TokenStore


class TestTokenStore:
    def test_add_and_get_summary(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_tokens("alice", 100, 50, 0.01)
        store.add_tokens("alice", 200, 100, 0.02)
        store.add_tokens("bob", 300, 150, 0.03)

        summary = store.get_summary()
        assert summary["per_user"]["alice"]["input_tokens"] == 300
        assert summary["per_user"]["alice"]["output_tokens"] == 150
        assert summary["per_user"]["bob"]["input_tokens"] == 300
        assert summary["all_users"]["input_tokens"] == 600
        assert summary["all_users"]["output_tokens"] == 300
        assert abs(summary["all_users"]["cost_usd"] - 0.06) < 0.001

    def test_empty_store(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "nonexistent" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        summary = store.get_summary()
        assert summary["per_user"] == {}
        assert summary["all_users"]["input_tokens"] == 0

    def test_single_user(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_tokens("alice", 500, 200, 0.05)

        summary = store.get_summary()
        assert len(summary["per_user"]) == 1
        assert summary["per_user"]["alice"]["input_tokens"] == 500
        assert summary["per_user"]["alice"]["output_tokens"] == 200
        assert abs(summary["per_user"]["alice"]["cost_usd"] - 0.05) < 0.001

    def test_zero_tokens(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_tokens("alice", 0, 0, 0.0)

        summary = store.get_summary()
        assert summary["per_user"]["alice"]["input_tokens"] == 0
        assert summary["per_user"]["alice"]["output_tokens"] == 0
        assert summary["per_user"]["alice"]["cost_usd"] == 0.0

    def test_large_token_counts(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_tokens("alice", 1_000_000, 500_000, 100.0)
        store.add_tokens("alice", 2_000_000, 1_000_000, 200.0)

        summary = store.get_summary()
        assert summary["per_user"]["alice"]["input_tokens"] == 3_000_000
        assert summary["per_user"]["alice"]["output_tokens"] == 1_500_000

    def test_persistence_across_instances(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store1 = TokenStore()
        store1.add_tokens("alice", 100, 50, 0.01)

        store2 = TokenStore()
        store2.add_tokens("alice", 200, 100, 0.02)

        summary = store2.get_summary()
        assert summary["per_user"]["alice"]["input_tokens"] == 300

    def test_corrupt_file_recovery(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        os.makedirs(os.path.dirname(usage_path), exist_ok=True)
        with open(usage_path, "w") as f:
            f.write("NOT VALID JSON")

        store = TokenStore()
        summary = store.get_summary()
        assert summary["per_user"] == {}

    def test_malformed_data_structure(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        os.makedirs(os.path.dirname(usage_path), exist_ok=True)
        with open(usage_path, "w") as f:
            json.dump({"wrong_key": "wrong_value"}, f)

        store = TokenStore()
        # Missing "users" key should reset to empty
        summary = store.get_summary()
        assert summary["per_user"] == {}

    def test_many_users(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        for i in range(50):
            store.add_tokens(f"user_{i}", 10, 5, 0.001)

        summary = store.get_summary()
        assert len(summary["per_user"]) == 50
        assert summary["all_users"]["input_tokens"] == 500
        assert summary["all_users"]["output_tokens"] == 250

    def test_cost_precision(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_tokens("alice", 1, 1, 0.000001)
        store.add_tokens("alice", 1, 1, 0.000002)

        summary = store.get_summary()
        assert abs(summary["per_user"]["alice"]["cost_usd"] - 0.000003) < 1e-10


class TestTokenStoreStepTracking:
    def test_add_step_tokens(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_step_tokens("alice", "sess1", "planner", 100, 50, 0.01)
        store.add_step_tokens("alice", "sess1", "coder", 500, 200, 0.05)

        breakdown = store.get_session_breakdown("alice", "sess1")
        assert breakdown["steps"]["planner"]["input_tokens"] == 100
        assert breakdown["steps"]["planner"]["output_tokens"] == 50
        assert breakdown["steps"]["coder"]["input_tokens"] == 500
        assert breakdown["steps"]["coder"]["output_tokens"] == 200
        assert breakdown["total_input"] == 600
        assert breakdown["total_output"] == 250
        assert abs(breakdown["total_cost"] - 0.06) < 0.001

    def test_add_step_tokens_accumulates(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_step_tokens("alice", "sess1", "coder", 100, 50, 0.01)
        store.add_step_tokens("alice", "sess1", "coder", 200, 100, 0.02)

        breakdown = store.get_session_breakdown("alice", "sess1")
        assert breakdown["steps"]["coder"]["input_tokens"] == 300
        assert breakdown["steps"]["coder"]["output_tokens"] == 150

    def test_get_session_breakdown_nonexistent(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        breakdown = store.get_session_breakdown("alice", "nonexistent")
        assert breakdown["steps"] == {}
        assert breakdown["total_input"] == 0
        assert breakdown["total_output"] == 0
        assert breakdown["total_cost"] == 0.0

    def test_step_tokens_creates_user(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_step_tokens("newuser", "sess1", "reviewer", 50, 25, 0.005)

        breakdown = store.get_session_breakdown("newuser", "sess1")
        assert breakdown["steps"]["reviewer"]["input_tokens"] == 50

    def test_multiple_sessions(self, tmp_path, monkeypatch):
        usage_path = str(tmp_path / "usage" / "token_usage.json")
        monkeypatch.setattr(ts_module, "USAGE_PATH", usage_path)

        store = TokenStore()
        store.add_step_tokens("alice", "sess1", "planner", 100, 50, 0.01)
        store.add_step_tokens("alice", "sess2", "planner", 200, 100, 0.02)

        b1 = store.get_session_breakdown("alice", "sess1")
        b2 = store.get_session_breakdown("alice", "sess2")
        assert b1["total_input"] == 100
        assert b2["total_input"] == 200
