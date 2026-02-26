import pytest

from src.agents.orchestrator import BOBBIEOrchestrator


def test_duplicate_control_assignment_raises():
    orch = BOBBIEOrchestrator()
    # Assign AC-2 to two families (AC and AU) to simulate bad plan
    bad_plan = {"AC": ["AC-2"], "AU": ["AC-2"]}
    with pytest.raises(ValueError):
        orch.run(bad_plan, context={})


def test_routing_mismatch_returns_error():
    # Directly instantiate an agent and call assess_control with mismatched control id
    from src.agents.base_family_agent import BaseFamilyAgent

    class FakeAgent(BaseFamilyAgent):
        family_id = "ZZ"

        def collect_evidence(self, control_id, context):
            return {"status": "PASS", "findings": [], "risk_level": "LOW"}

    agent = FakeAgent()
    res = agent.assess_control("AC-2", context={})
    assert res.get("status") == "ERROR"
    assert "routed to family" in (res.get("findings") or [""])[0]
