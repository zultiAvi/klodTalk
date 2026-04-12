"""Tests for WebSocket message protocol parsing (no real server needed)."""

import hashlib
import json

import pytest


class TestProtocolMessages:
    def test_hello_message_format(self):
        msg = {
            "type": "hello",
            "name": "alice",
            "password_hash": hashlib.sha256(b"secret").hexdigest(),
        }
        serialized = json.dumps(msg)
        parsed = json.loads(serialized)
        assert parsed["type"] == "hello"
        assert parsed["name"] == "alice"
        assert len(parsed["password_hash"]) == 64

    def test_text_message_format(self):
        msg = {
            "type": "text",
            "project": "my-project",
            "content": "implement feature X",
        }
        parsed = json.loads(json.dumps(msg))
        assert parsed["type"] == "text"
        assert parsed["project"] == "my-project"
        assert parsed["content"] == "implement feature X"

    def test_projects_message_format(self):
        msg = {
            "type": "projects",
            "projects": [
                {"name": "project1", "description": "First project"},
                {"name": "project2", "description": "Second project"},
            ],
        }
        parsed = json.loads(json.dumps(msg))
        assert parsed["type"] == "projects"
        assert len(parsed["projects"]) == 2
        assert parsed["projects"][0]["name"] == "project1"

    def test_response_message_format(self):
        msg = {
            "type": "response",
            "project": "my-project",
            "content": "Task completed successfully.",
        }
        parsed = json.loads(json.dumps(msg))
        assert parsed["type"] == "response"
        assert parsed["project"] == "my-project"

    def test_password_hash_consistency(self):
        password = "my_password"
        hash1 = hashlib.sha256(password.encode("utf-8")).hexdigest()
        hash2 = hashlib.sha256(password.encode("utf-8")).hexdigest()
        assert hash1 == hash2
        assert len(hash1) == 64


class TestProtocolEdgeCases:
    def test_empty_content(self):
        msg = {"type": "text", "project": "a", "content": ""}
        parsed = json.loads(json.dumps(msg))
        assert parsed["content"] == ""

    def test_unicode_content(self):
        msg = {"type": "text", "project": "a", "content": "\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd"}
        parsed = json.loads(json.dumps(msg))
        assert parsed["content"] == "\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd"

    def test_large_content(self):
        msg = {"type": "text", "project": "a", "content": "x" * 100_000}
        parsed = json.loads(json.dumps(msg))
        assert len(parsed["content"]) == 100_000

    def test_multiline_content(self):
        msg = {"type": "text", "project": "a", "content": "line1\nline2\nline3"}
        parsed = json.loads(json.dumps(msg))
        assert "\n" in parsed["content"]

    def test_special_chars_in_name(self):
        msg = {"type": "hello", "name": "alice-bob_123", "password_hash": "a" * 64}
        parsed = json.loads(json.dumps(msg))
        assert parsed["name"] == "alice-bob_123"

    def test_empty_projects_list(self):
        msg = {"type": "projects", "projects": []}
        parsed = json.loads(json.dumps(msg))
        assert parsed["projects"] == []

    def test_project_with_empty_description(self):
        msg = {"type": "projects", "projects": [{"name": "a", "description": ""}]}
        parsed = json.loads(json.dumps(msg))
        assert parsed["projects"][0]["description"] == ""

    def test_response_with_newlines(self):
        msg = {"type": "response", "project": "a", "content": "line1\nline2\n```code```\n"}
        parsed = json.loads(json.dumps(msg))
        assert "```code```" in parsed["content"]

    def test_different_hash_for_different_passwords(self):
        h1 = hashlib.sha256(b"password1").hexdigest()
        h2 = hashlib.sha256(b"password2").hexdigest()
        assert h1 != h2

    def test_json_roundtrip_preserves_types(self):
        msg = {
            "type": "projects",
            "projects": [{"name": "a", "description": "d"}],
        }
        parsed = json.loads(json.dumps(msg))
        assert isinstance(parsed["projects"], list)
        assert isinstance(parsed["projects"][0], dict)
        assert isinstance(parsed["type"], str)


class TestProtocolValidation:
    """Test that message structures can be validated."""

    REQUIRED_FIELDS = {
        "hello": {"type", "name", "password_hash"},
        "text": {"type", "project", "content"},
        "projects": {"type", "projects"},
        "response": {"type", "project", "content"},
    }

    def _validate(self, msg):
        msg_type = msg.get("type")
        if msg_type not in self.REQUIRED_FIELDS:
            return False
        return self.REQUIRED_FIELDS[msg_type].issubset(msg.keys())

    def test_valid_hello(self):
        assert self._validate({"type": "hello", "name": "a", "password_hash": "h"})

    def test_valid_text(self):
        assert self._validate({"type": "text", "project": "a", "content": "c"})

    def test_valid_projects(self):
        assert self._validate({"type": "projects", "projects": []})

    def test_valid_response(self):
        assert self._validate({"type": "response", "project": "a", "content": "c"})

    def test_invalid_missing_name(self):
        assert not self._validate({"type": "hello", "password_hash": "h"})

    def test_invalid_missing_content(self):
        assert not self._validate({"type": "text", "project": "a"})

    def test_invalid_unknown_type(self):
        assert not self._validate({"type": "unknown"})

    def test_invalid_empty_message(self):
        assert not self._validate({})
