from pathlib import Path

from src.agents.orchestrator import BOBBIEOrchestrator
from src.tools.aws_tools import detect_hourly_gaps_anomalies, reconcile_inventory


def test_detect_hourly_gaps_and_anomalies() -> None:
    hourly = [10] * 24
    hourly[3] = 0
    hourly[12] = 200

    stats = detect_hourly_gaps_anomalies(hourly, z_threshold=2.0)

    assert stats["valid"] is True
    assert 3 in stats["gap_hours"]
    assert 12 in stats["anomaly_hours"]


def test_reconcile_inventory_reports_missing_and_unmanaged() -> None:
    result = reconcile_inventory(
        expected=["i-001", "i-002"],
        discovered=["i-002", "i-003"],
    )

    assert result["missing_count"] == 1
    assert result["unmanaged_count"] == 1
    assert result["missing_assets"] == ["i-001"]
    assert result["unmanaged_assets"] == ["i-003"]


def test_cm8_uses_ssm_inventory_context_when_control_evidence_missing() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "aws": {
            "ssm": {
                "inventory_expected": ["i-001", "i-002"],
                "inventory_discovered": ["i-001", "i-003"],
            }
        },
    }

    result = orchestrator.run({"CM": ["CM-8"]}, context=context)
    control = result["families"]["CM"]["controls"]["CM-8"]

    assert control["status"] == "FAIL"
    assert any("Inventory records missing" in finding for finding in control["findings"])
    assert any("shadow IT" in finding for finding in control["findings"])


def test_si2_uses_patch_and_kev_context_for_findings() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "aws": {
            "ssm": {
                "patches": [
                    {
                        "cve": "CVE-2025-0001",
                        "severity": "CRITICAL",
                        "days_open": 20,
                        "compensating_control": False,
                    }
                ],
                "kev_vulnerabilities": [{"cveID": "CVE-2025-0001"}],
            }
        },
    }

    result = orchestrator.run({"SI": ["SI-2"]}, context=context)
    control = result["families"]["SI"]["controls"]["SI-2"]

    assert control["status"] == "FAIL"
    assert control["evidence"]["effectiveness"] == "INEFFECTIVE"
    patches = control["evidence"]["control_evidence"]["patches"]
    assert any(item.get("in_kev", False) for item in patches)


def test_si4_anomaly_is_reported_from_control_evidence() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    context = {
        "repo_root": str(root),
        "control_evidence": {
            "SI-4": {
                "hourly_event_counts": [10] * 24,
                "anomaly_hours": [8],
            }
        },
    }

    result = orchestrator.run({"SI": ["SI-4"]}, context=context)
    control = result["families"]["SI"]["controls"]["SI-4"]

    assert control["status"] == "FAIL"
    assert any("Log volume anomalies" in finding for finding in control["findings"])
