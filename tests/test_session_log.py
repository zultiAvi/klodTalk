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


# ── Integration tests covering server.py interaction with session_log ─────────
# These tests guard the two-bug fix for closed-session-reopen duplication and
# hook-event leakage into the client view. Import server lazily because it has
# module-level side effects; isolate writes via tmp env vars.

@pytest.fixture
def server_module(tmp_path, monkeypatch):
    """Import server.server with isolated workspace/log directories."""
    monkeypatch.setenv("KLODTALK_TEMP_BASE", str(tmp_path / "ws"))
    monkeypatch.setenv("KLODTALK_LOG_BASE", str(tmp_path / "logs"))
    # Force a fresh import so the env vars take effect even if a previous test
    # already imported server.
    import session_log
    importlib.reload(session_log)
    import server
    importlib.reload(server)
    return server


def test_session_to_dict_filters_hook_events(server_module, tmp_path):
    """role='hook' entries in events.jsonl must NOT appear in the messages
    list returned to clients on history fetch."""
    server = server_module
    sid = "ses_hook01"
    # Arrange: persistent log with a mix of roles.
    server.session_log.log_event(sid, "user", "hello")
    server.session_log.log_event(sid, "hook", '{"tool":"Read","path":"/x"}')
    server.session_log.log_event(sid, "agent", "world")
    server.session_log.log_event(sid, "hook", '{"tool":"Edit"}')

    # Build a minimal Session-like stand-in. _session_to_dict only reads
    # attributes; it does not call into session_manager.
    class _S:
        session_id = sid
        project_name = "p"
        git_branch = "b"
        status = "open"
        created_at = ""
        closed_at = ""
        user_name = "u"
        users = ["u"]
        workspace_path = str(tmp_path / "ws")
        system = False
        comment = ""

    d = server._session_to_dict(_S(), include_messages=True)
    msgs = d["messages"]
    roles = [m["role"] for m in msgs]
    assert "hook" not in roles, f"hook role leaked into messages: {roles}"
    assert roles == ["user", "agent"]


def test_broadcast_does_not_double_write_when_log_to_session_false(server_module):
    """Explicit log_event + default-arg _broadcast_to_session_users must
    produce exactly ONE line in events.jsonl, not two."""
    import asyncio
    server = server_module
    sid = "ses_dup01"

    # Register a fake session so _broadcast_to_session_users does not early-out.
    class _S:
        session_id = sid
        users = []  # no connected clients, send loop is a no-op
        project_name = "p"

    server.session_manager._sessions[sid] = _S()

    # Explicit log_event (mirrors what every role handler in server.py does
    # immediately before broadcasting).
    server.session_log.log_event(sid, "user", "hello")
    # Broadcast with default log_to_session=False — must NOT mirror.
    asyncio.run(server._broadcast_to_session_users(sid, {
        "type": "new_message",
        "session_id": sid,
        "role": "user",
        "content": "hello",
    }))

    events = server.session_log.read_events(sid)
    assert len(events) == 1, f"expected 1 event, got {len(events)}: {events}"
    assert events[0]["role"] == "user"
    assert events[0]["content"] == "hello"


def test_nightly_start_broadcast_single_write(server_module):
    """The nightly-routine start path logs the message via session_log.log_event
    AND then broadcasts it. The broadcast must NOT mirror — otherwise every
    nightly run writes the same content twice into events.jsonl, which then
    surfaces as duplicate "Nightly routine starting" lines on reconnect.

    This mirrors the production sequence at server/server.py:~3510 (log_event)
    + ~3516 (broadcast). After the fix, the broadcast no longer passes
    log_to_session=True, so exactly one row lands in events.jsonl.
    """
    import asyncio
    server = server_module
    sid = "ses_nightly01"

    class _S:
        session_id = sid
        users = []
        project_name = "system"

    server.session_manager._sessions[sid] = _S()

    body = "Nightly routine starting: scanning Claude/Anthropic channels and GitHub for improvements..."
    # Step 1 — explicit log_event (matches server.py:~3510).
    server.session_log.log_event(sid, "system", body)
    # Step 2 — broadcast with default log_to_session=False (matches the fixed
    # server.py:~3516 call site).
    asyncio.run(server._broadcast_to_session_users(sid, {
        "type": "new_message",
        "session_id": sid,
        "project": "system",
        "role": "system",
        "content": body,
    }))

    events = server.session_log.read_events(sid)
    assert len(events) == 1, f"nightly broadcast double-wrote: {events}"
    assert events[0]["role"] == "system"
    assert events[0]["content"].startswith("Nightly routine starting")


def test_session_to_dict_archive_branch_filters_hook_events(server_module, tmp_path):
    """Closed-session reopen reads from the archive ``session.jsonl`` when the
    persistent ``events.jsonl`` is empty. The archive branch must apply the
    same ``role == "hook"`` filter as the persistent branch — otherwise hook
    rows leak into the client view on reopen of legacy sessions."""
    import json as _json
    server = server_module
    sid = "ses_archive_hook01"

    # Stage an archive directory with one normal + one hook row.
    archive_dir = tmp_path / "archive" / sid
    archive_dir.mkdir(parents=True)
    archive_file = archive_dir / "session.jsonl"
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(_json.dumps({"timestamp": "t0", "role": "user", "content": "hello"}) + "\n")
        f.write(_json.dumps({"timestamp": "t1", "role": "hook", "content": '{"tool":"Read"}'}) + "\n")
        f.write(_json.dumps({"timestamp": "t2", "role": "agent", "content": "world"}) + "\n")

    # Stub session_manager.get_archive_path to point at the staged dir.
    server.session_manager.get_archive_path = lambda s: str(archive_dir)  # type: ignore

    class _S:
        session_id = sid
        project_name = "p"
        git_branch = "b"
        status = "closed"
        created_at = ""
        closed_at = ""
        user_name = "u"
        users = ["u"]
        workspace_path = str(tmp_path / "ws_missing")  # intentionally missing
        system = False
        comment = ""

    # Ensure the persistent log is empty so the archive branch is exercised.
    assert server.session_log.read_events(sid) == []

    d = server._session_to_dict(_S(), include_messages=True)
    msgs = d["messages"]
    roles = [m["role"] for m in msgs]
    assert "hook" not in roles, f"archive hook row leaked into messages: {roles}"
    assert roles == ["user", "agent"], roles


def test_broadcast_mirrors_when_log_to_session_true(server_module):
    """Opt-in path: log_to_session=True must still mirror lifecycle/error
    payloads that have no peer explicit log_event."""
    import asyncio
    server = server_module
    sid = "ses_mirror01"

    class _S:
        session_id = sid
        users = []
        project_name = "p"

    server.session_manager._sessions[sid] = _S()

    asyncio.run(server._broadcast_to_session_users(sid, {
        "type": "session_working",
        "session_id": sid,
        "working": True,
    }, log_to_session=True))

    events = server.session_log.read_events(sid)
    assert len(events) == 1
    assert events[0].get("type") == "session_working" or events[0].get("role") == "system"
