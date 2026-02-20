from pathlib import Path

from src.agents.orchestrator import BOBBIEOrchestrator


def test_ac2_fails_when_evidence_missing() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    result = orchestrator.run({"AC": ["AC-2"]}, context={"repo_root": str(root)})
    control = result["families"]["AC"]["controls"]["AC-2"]

    assert control["status"] == "FAIL"
    assert control["evidence"]["effectiveness"] == "INEFFECTIVE"
    assert any("NOT MET" in finding for finding in control["findings"])


def test_ac2_passes_with_authorized_ticket_evidence() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "AC-2": {
                "account_events": [
                    {"account_id": "svc-app-01"},
                ],
                "approved_tickets": [
                    {"account_id": "svc-app-01", "isso_approved": True},
                ],
                "status_change_notifications": True,
            }
        },
    }

    result = orchestrator.run({"AC": ["AC-2"]}, context=context)
    control = result["families"]["AC"]["controls"]["AC-2"]

    assert control["status"] == "PASS"
    assert control["findings"] == []
    assert control["evidence"]["effectiveness"] == "EFFECTIVE"


def test_ia5_fails_when_policy_thresholds_not_met() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "IA-5": {
                "policy": {
                    "MinimumLength": 8,
                    "ComplexityEnabled": False,
                    "PasswordHistory": 10,
                    "MaximumAge": 180,
                }
            }
        },
    }

    result = orchestrator.run({"IA": ["IA-5"]}, context=context)
    control = result["families"]["IA"]["controls"]["IA-5"]

    assert control["status"] == "FAIL"
    assert len(control["findings"]) >= 2
