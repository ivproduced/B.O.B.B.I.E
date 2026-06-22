import json
from types import SimpleNamespace

from src.agents.base_family_agent import BaseFamilyAgent


class DummyAgent(BaseFamilyAgent):
    family_id = "TT"

    def collect_evidence(self, control_id: str, context: dict):
        return {"status": "FAIL", "findings": ["evidence missing"], "risk_level": "LOW"}


def make_client(response_content: str):
    class C:
        def invoke(self, prompt: str):
            return SimpleNamespace(content=response_content)

    return C()


def test_nova_suggestion_not_applied_by_default(monkeypatch):
    client = make_client(json.dumps({
        "suggested_status": "PASS",
        "suggested_risk": "MEDIUM",
        "confidence": 0.95,
        "explanation": "Looks low risk."
    }))
    monkeypatch.setattr("src.models.nova_client.create_nova_client", lambda region_name=None: client)

    agent = DummyAgent()
    ctx = {"nova_narrative": True, "apply_nova_suggestions": False, "nova_confidence_threshold": 0.9}
    res = agent.assess_control("TT-1", ctx)

    assert "nova_suggestion" in res
    assert res["status"] == "FAIL"
    assert not res.get("nova_suggestion_applied", False)


def test_nova_suggestion_applied_when_flag_and_confident(monkeypatch):
    """Nova cannot auto-promote FAIL→PASS even when apply_nova_suggestions is True.

    LLM08/AA02: Excessive agency — an LLM must never unilaterally clear a
    compliance failure. The suggestion is recorded but the status stays FAIL,
    and the blocked attempt is flagged in the suggestion for human review.
    """
    client = make_client(json.dumps({
        "suggested_status": "PASS",
        "suggested_risk": "MEDIUM",
        "confidence": 0.95,
        "explanation": "Looks low risk."
    }))
    monkeypatch.setattr("src.models.nova_client.create_nova_client", lambda region_name=None: client)

    agent = DummyAgent()
    ctx = {"nova_narrative": True, "apply_nova_suggestions": True, "nova_confidence_threshold": 0.9}
    res = agent.assess_control("TT-1", ctx)

    # FAIL→PASS promotion is blocked; the deterministic FAIL result must be preserved.
    assert res["status"] == "FAIL", "Nova must not auto-promote FAIL→PASS (LLM08/AA02)"
    assert not res.get("nova_suggestion_applied", False)
    # The suggestion is still attached for a human reviewer, with the block flag.
    assert "nova_suggestion" in res
    assert res["nova_suggestion"].get("_fail_to_pass_blocked"), (
        "Blocked FAIL→PASS must be flagged in nova_suggestion for human review"
    )
    assert res["nova_suggestion"].get("suggested_status") is None


def test_nova_suggestion_not_applied_if_low_confidence(monkeypatch):
    client = make_client(json.dumps({
        "suggested_status": "PASS",
        "suggested_risk": "MEDIUM",
        "confidence": 0.5,
        "explanation": "Low confidence."
    }))
    monkeypatch.setattr("src.models.nova_client.create_nova_client", lambda region_name=None: client)

    agent = DummyAgent()
    ctx = {"nova_narrative": True, "apply_nova_suggestions": True, "nova_confidence_threshold": 0.9}
    res = agent.assess_control("TT-1", ctx)

    assert res["status"] == "FAIL"
    assert not res.get("nova_suggestion_applied", False)
