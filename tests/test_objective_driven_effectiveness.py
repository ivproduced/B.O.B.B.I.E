from pathlib import Path
import json

from src.agents.orchestrator import BOBBIEOrchestrator
from src.tools import get_control_assessment_objectives


def test_ac2_objectives_are_extracted_from_catalog() -> None:
    root = Path(__file__).resolve().parent.parent
    objectives = get_control_assessment_objectives("AC-2", {"repo_root": str(root)})
    assert len(objectives) > 0
    assert any(item["objective_id"].lower().startswith("ac-2_obj") for item in objectives)


def test_ac2_effectiveness_reports_objective_trace() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "AC-2": {
                "account_events": [{"account_id": "svc-app-01"}],
                "approved_tickets": [{"account_id": "svc-app-01", "isso_approved": True}],
                "status_change_notifications": True,
            }
        },
    }

    result = orchestrator.run({"AC": ["AC-2"]}, context=context)
    control = result["families"]["AC"]["controls"]["AC-2"]

    assert control["status"] == "PASS"
    assert control["evidence"]["effectiveness"] in {"EFFECTIVE", "INEFFECTIVE"}
    assert len(control["evidence"]["objective_results"]) > 0


def test_ac2_effectiveness_fails_when_objective_evidence_missing() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    result = orchestrator.run({"AC": ["AC-2"]}, context={"repo_root": str(root), "control_evidence": {"AC-2": {}}})
    control = result["families"]["AC"]["controls"]["AC-2"]

    assert control["status"] == "FAIL"
    assert control["evidence"]["effectiveness"] == "INEFFECTIVE"


def test_ac2_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_ac2.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("AC-2", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]
    assert objectives[0]["objective_id"] == payload["objectives"][0]["objective_id"]


def test_au3_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_au3.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("AU-3", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]


def test_si2_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_si2.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("SI-2", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]


def test_au3_effectiveness_reports_objective_trace() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "AU-3": {
                "records": [
                    {
                        "timestamp": "2026-02-14T12:00:00Z",
                        "event_type": "AUTH",
                        "subject": "user1",
                        "outcome": "SUCCESS",
                        "source_ip": "10.0.0.10",
                    }
                ],
                "pii_detections": 0,
            }
        },
    }

    result = orchestrator.run({"AU": ["AU-3"]}, context=context)
    control = result["families"]["AU"]["controls"]["AU-3"]

    assert control["status"] == "PASS"
    assert control["evidence"]["effectiveness"] == "EFFECTIVE"
    assert len(control["evidence"]["objective_results"]) > 0


def test_si2_effectiveness_fails_with_overdue_critical_without_compensating_control() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "SI-2": {
                "patches": [
                    {
                        "cve": "CVE-2025-0001",
                        "severity": "CRITICAL",
                        "days_open": 45,
                        "compensating_control": False,
                    }
                ]
            }
        },
    }

    result = orchestrator.run({"SI": ["SI-2"]}, context=context)
    control = result["families"]["SI"]["controls"]["SI-2"]

    assert control["status"] == "FAIL"
    assert control["evidence"]["effectiveness"] == "INEFFECTIVE"
    assert len(control["evidence"]["objective_results"]) > 0


def test_ia5_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_ia5.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("IA-5", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]


def test_ra5_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_ra5.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("RA-5", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]


def test_ia5_effectiveness_reports_objective_trace() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "IA-5": {
                "policy": {
                    "MinimumLength": 14,
                    "ComplexityEnabled": True,
                    "PasswordHistory": 24,
                    "MaximumAge": 60,
                },
                "weak_algorithms": [],
            }
        },
    }

    result = orchestrator.run({"IA": ["IA-5"]}, context=context)
    control = result["families"]["IA"]["controls"]["IA-5"]

    assert control["status"] == "PASS"
    assert control["evidence"]["effectiveness"] == "EFFECTIVE"
    assert len(control["evidence"]["objective_results"]) > 0


def test_ra5_effectiveness_fails_with_sla_and_kev_issues() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "RA-5": {
                "vulnerabilities": [
                    {
                        "cve": "CVE-2025-9999",
                        "cvss_score": 9.8,
                        "days_open": 45,
                        "in_kev": True,
                    }
                ],
                "scan_coverage": 0.80,
                "scan_age_hours": 120,
            }
        },
    }

    result = orchestrator.run({"RA": ["RA-5"]}, context=context)
    control = result["families"]["RA"]["controls"]["RA-5"]

    assert control["status"] == "FAIL"
    assert control["evidence"]["effectiveness"] == "INEFFECTIVE"
    assert len(control["evidence"]["objective_results"]) > 0


def test_pl2_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_pl2.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("PL-2", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]


def test_pm9_objectives_prefer_fixture_file_when_available() -> None:
    root = Path(__file__).resolve().parent.parent
    fixture = root / "data" / "oscal_samples" / "objectives_pm9.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    objectives = get_control_assessment_objectives("PM-9", {"repo_root": str(root)})
    assert len(objectives) == payload["total_objectives"]


def test_pl2_effectiveness_reports_objective_trace() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "PL-2": {
                "sections_present": ["system-characteristics", "control-implementation", "system-implementation", "metadata"],
                "missing_baseline_controls": 0,
                "stale_approvals": 0,
            }
        },
    }

    result = orchestrator.run({"PL": ["PL-2"]}, context=context)
    control = result["families"]["PL"]["controls"]["PL-2"]

    assert control["status"] == "PASS"
    assert control["evidence"]["effectiveness"] == "EFFECTIVE"
    assert len(control["evidence"]["objective_results"]) > 0


def test_pm9_effectiveness_fails_for_invalid_risk_evidence() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "PM-9": {
                "risks": [
                    {
                        "id": "R-001",
                        "likelihood": 3,
                        "impact": 3,
                        "score": 4,
                        "approved": False,
                        "mitigation": "",
                    }
                ]
            }
        },
    }

    result = orchestrator.run({"PM": ["PM-9"]}, context=context)
    control = result["families"]["PM"]["controls"]["PM-9"]

    assert control["status"] == "FAIL"
    assert control["evidence"]["effectiveness"] == "INEFFECTIVE"
    assert len(control["evidence"]["objective_results"]) > 0
