"""Unit tests for server/session_log.py."""

import builtins
import importlib
import json
import os

import pytest


@pytest.fixture
def fresh_session_log(tmp_path, monkeypatch):
    """Reload session_log against a temporary KLODTALK_LOG_BASE."""
    monkeypatch.setenv("KLODTALK_LOG_BASE", str(tmp_path / "klodTalk_logs"))
    import session_log
    importlib.reload(session_log)
    return session_log


def test_log_event_creates_dir_and_file(fresh_session_log):
    sl = fresh_session_log
    sl.log_event("abc1234", "user", "hello world")
    d = os.path.join(sl.LOG_BASE, "abc1234.klodTalk")
    assert os.path.isdir(d)
    events_file = os.path.join(d, "events.jsonl")
    log_file = os.path.join(d, "log.txt")
    assert os.path.isfile(events_file)
    assert os.path.isfile(log_file)
    line = open(events_file).read().strip()
    entry = json.loads(line)
    assert entry["role"] == "user"
    assert entry["content"] == "hello world"
    assert "timestamp" in entry
    assert "[user]" in open(log_file).read()


def test_init_session_log_writes_meta_once(fresh_session_log):
    sl = fresh_session_log
    sl.init_session_log("sess0001", project_name="proj", user_name="alice",
                        created_at="2026-01-01T00:00:00Z")
    meta_path = os.path.join(sl.LOG_BASE, "sess0001.klodTalk", "meta.json")
    assert os.path.isfile(meta_path)
    meta = json.load(open(meta_path))
    assert meta["session_id"] == "sess0001"
    assert meta["project_name"] == "proj"
    assert meta["user_name"] == "alice"
    # Second call must not overwrite
    sl.init_session_log("sess0001", project_name="other", user_name="bob")
    meta = json.load(open(meta_path))
    assert meta["project_name"] == "proj"


def test_read_events_returns_appended_events(fresh_session_log):
    sl = fresh_session_log
    sid = "ses12345"
    sl.log_event(sid, "user", "first")
    sl.log_event(sid, "agent", "second", model="opus")
    events = sl.read_events(sid)
    assert len(events) == 2
    assert events[0]["content"] == "first"
    assert events[1]["content"] == "second"
    assert events[1]["model"] == "opus"


def test_read_events_missing_dir_returns_empty_list(fresh_session_log):
    sl = fresh_session_log
    assert sl.read_events("does_not_exist") == []


def test_log_event_swallows_errors(fresh_session_log, monkeypatch):
    sl = fresh_session_log
    real_open = builtins.open

    def boom(*a, **kw):
        # Raise on writes only — meta read still works.
        if len(a) > 1 and "a" in str(a[1]):
            raise OSError("disk full")
        return real_open(*a, **kw)

    monkeypatch.setattr(builtins, "open", boom)
    # Must not raise
    sl.log_event("ses_error", "user", "should not raise")


def test_append_raw_writes_delimiter(fresh_session_log):
    sl = fresh_session_log
    sid = "ses_raw01"
    sl.append_raw(sid, "stdout", "hello\n")
    sl.append_raw(sid, "stdout", "world\n")
    path = os.path.join(sl.LOG_BASE, f"{sid}.klodTalk", "agent_stdout.log")
    body = open(path).read()
    assert "--- exec @" in body
    # Two delimiter lines for two appends
    assert body.count("--- exec @") == 2
    assert "hello" in body and "world" in body


def test_append_raw_ignores_unknown_stream(fresh_session_log):
    sl = fresh_session_log
    sid = "ses_raw02"
    sl.append_raw(sid, "weird", "data")
    # No file should have been created beyond the dir itself.
    d = os.path.join(sl.LOG_BASE, f"{sid}.klodTalk")
    if os.path.isdir(d):
        assert not any(name.startswith("agent_") for name in os.listdir(d))


def test_log_event_truncates_human_line_only(fresh_session_log):
    sl = fresh_session_log
    sid = "ses_long"
    big = "x" * 10000
    sl.log_event(sid, "agent", big)
    # JSONL keeps full content
    events = sl.read_events(sid)
    assert events[0]["content"] == big
    # log.txt is truncated
    log_text = open(os.path.join(sl.LOG_BASE, f"{sid}.klodTalk", "log.txt")).read()
    assert "[truncated]" in log_text


def test_purge_removes_directory(fresh_session_log):
    sl = fresh_session_log
    sid = "ses_purge"
    sl.log_event(sid, "user", "hi")
    d = os.path.join(sl.LOG_BASE, f"{sid}.klodTalk")
    assert os.path.isdir(d)
    assert sl.purge(sid) is True
    assert not os.path.isdir(d)
    # Purging a non-existent dir is a no-op success
    assert sl.purge(sid) is True


def test_log_event_empty_session_id_is_noop(fresh_session_log):
    sl = fresh_session_log
    # Must not raise and must not create a stray dir
    sl.log_event("", "user", "ignored")
    # Base dir may exist from a previous test, but no ".klodTalk" entry for ""
    # should be created.
    if os.path.isdir(sl.LOG_BASE):
        assert ".klodTalk" not in os.listdir(sl.LOG_BASE)
