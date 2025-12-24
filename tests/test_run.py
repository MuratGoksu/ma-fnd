import json
import importlib.util
import pytest

from main import run


def test_run_mock_rule_writes_log_and_returns_verdict(tmp_path, monkeypatch):
    """Run main.run with mock source and rule judge in an isolated tmp dir.

    Verifies:
    - The returned verdict is one of REAL/FAKE/UNSURE
    - A logs/run.jsonl file is created
    - The last JSONL entry matches the returned verdict
    """
    # Ensure run writes logs into tmp_path instead of repository
    monkeypatch.chdir(tmp_path)

    verdict, record = run(source="mock", judge_choice="rule")

    assert verdict in {"REAL", "FAKE", "UNSURE"}
    assert isinstance(record, dict)
    assert record.get("headline") is not None

    p = tmp_path / "logs" / "run.jsonl"
    assert p.exists(), "logs/run.jsonl should exist"

    content = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) >= 1
    last = json.loads(content[-1])
    assert last.get("verdict") == verdict


@pytest.mark.skipif(not importlib.util.find_spec("agents.judge_agent"), reason="LLM judge not available")
def test_run_llm_skipped_by_default(tmp_path, monkeypatch):
    # If LLM judge exists, we still skip here: running LLM would require API access
    pytest.skip("LLM judge exists but we skip running it in unit tests")
