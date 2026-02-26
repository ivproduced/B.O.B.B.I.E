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

    assert res["status"] == "PASS"
    assert res["risk_level"] == "MEDIUM"
    assert res.get("nova_suggestion_applied") is True
    assert res.get("_original_status") == "FAIL"
    assert res.get("_original_risk_level") == "LOW"


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
