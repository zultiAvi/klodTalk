"""Unit tests for run_agent.classify_refusal.

Covers the stop_reason/stop_details refusal classification added for the
Claude Platform API change (2026-06-02): a refusal with a null category on an
authorized workspace task is the signature of a hallucinated / workspace-auth
false-positive refusal, while a cyber/bio category is a genuine policy refusal.
"""

import run_agent


def test_normal_end_turn_is_not_refusal():
    data = {"stop_reason": "end_turn", "result": "done"}
    is_refusal, category, explanation = run_agent.classify_refusal(data)
    assert is_refusal is False
    assert category is None
    assert explanation == ""


def test_refusal_null_category_is_hallucinated_signature():
    data = {"stop_reason": "refusal", "stop_details": {"category": None,
                                                       "explanation": ""}}
    is_refusal, category, explanation = run_agent.classify_refusal(data)
    assert is_refusal is True
    assert category is None


def test_refusal_missing_stop_details_treated_as_null_category():
    data = {"stop_reason": "refusal"}
    is_refusal, category, explanation = run_agent.classify_refusal(data)
    assert is_refusal is True
    assert category is None
    assert explanation == ""


def test_refusal_cyber_category_is_genuine():
    data = {"stop_reason": "refusal",
            "stop_details": {"category": "cyber",
                             "explanation": "potential exploit code"}}
    is_refusal, category, explanation = run_agent.classify_refusal(data)
    assert is_refusal is True
    assert category == "cyber"
    assert explanation == "potential exploit code"


def test_refusal_bio_category_is_genuine():
    data = {"stop_reason": "refusal", "stop_details": {"category": "bio"}}
    is_refusal, category, explanation = run_agent.classify_refusal(data)
    assert is_refusal is True
    assert category == "bio"
    assert explanation == ""


def test_non_dict_input_is_not_refusal():
    is_refusal, category, explanation = run_agent.classify_refusal(None)  # type: ignore[arg-type]
    assert is_refusal is False
    assert category is None
    assert explanation == ""


def test_stop_details_none_is_treated_as_null_category():
    data = {"stop_reason": "refusal", "stop_details": None}
    is_refusal, category, explanation = run_agent.classify_refusal(data)
    assert is_refusal is True
    assert category is None


def test_log_refusal_writes_warning_for_null_category(tmp_path, monkeypatch, capsys):
    """A null-category refusal is logged to stderr and the refusal log file."""
    log_file = tmp_path / "refusal_events.log"
    monkeypatch.setattr(run_agent, "TEAM_CURRENT_DIR", str(tmp_path))
    monkeypatch.setattr(run_agent, "REFUSAL_LOG_FILE", str(log_file))

    run_agent.log_refusal({"stop_reason": "refusal"}, "single-agent")

    err = capsys.readouterr().err
    assert "WARNING [refusal:single-agent]" in err
    assert "authorization preamble" in err
    assert log_file.is_file()
    assert "null category" in log_file.read_text()


def test_log_refusal_surfaces_genuine_category(tmp_path, monkeypatch, capsys):
    log_file = tmp_path / "refusal_events.log"
    monkeypatch.setattr(run_agent, "TEAM_CURRENT_DIR", str(tmp_path))
    monkeypatch.setattr(run_agent, "REFUSAL_LOG_FILE", str(log_file))

    run_agent.log_refusal(
        {"stop_reason": "refusal",
         "stop_details": {"category": "cyber", "explanation": "exploit"}},
        "team-orchestrator",
    )

    err = capsys.readouterr().err
    assert "category=cyber" in err
    assert "exploit" in err


def test_log_refusal_noop_on_normal_run(tmp_path, monkeypatch, capsys):
    log_file = tmp_path / "refusal_events.log"
    monkeypatch.setattr(run_agent, "TEAM_CURRENT_DIR", str(tmp_path))
    monkeypatch.setattr(run_agent, "REFUSAL_LOG_FILE", str(log_file))

    run_agent.log_refusal({"stop_reason": "end_turn"}, "single-agent")

    assert capsys.readouterr().err == ""
    assert not log_file.is_file()
