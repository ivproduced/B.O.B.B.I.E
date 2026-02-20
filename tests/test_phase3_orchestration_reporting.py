from __future__ import annotations

import time
from pathlib import Path

import src.agents.orchestrator as orchestrator_module
from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils import ReportGenerator


class _SlowAgent:
    family_id = "PL"

    def assess_control(self, control_id: str, context: dict):
        time.sleep(0.05)
        return {
            "control_id": control_id,
            "status": "PASS",
            "findings": [],
            "recommendations": [],
            "risk_level": "LOW",
            "confidence_score": 1.0,
            "evidence": {},
        }

    def aggregate_family_results(self, results: dict):
        passed = sum(1 for value in results.values() if value.get("status") == "PASS")
        total = len(results)
        return type(
            "FamilyResult",
            (),
            {
                "controls": results,
                "summary": {"total_controls": total, "passed": passed, "failed": total - passed},
            },
        )()


def test_orchestrator_adds_phase3_summary_fields() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    result = orchestrator.run({"PL": ["PL-2"], "PM": ["PM-9"]}, context={"repo_root": str(root), "deterministic_run": True})

    summary = result["summary"]
    assert "compliance_score" in summary
    assert "prioritized_findings" in summary
    assert "poam_items" in summary
    assert summary["deterministic_mode"] is True


def test_orchestrator_timeout_isolation(monkeypatch) -> None:
    monkeypatch.setattr(orchestrator_module, "get_family_agent", lambda _family_id: _SlowAgent())

    orchestrator = BOBBIEOrchestrator()
    result = orchestrator.run(
        {"PL": ["PL-2"]},
        context={"orchestrator": {"control_timeout_seconds": 0.001, "max_workers": 1}},
    )

    control = result["families"]["PL"]["controls"]["PL-2"]
    assert control["status"] == "FAIL"
    assert any("timed out" in finding.lower() for finding in control["findings"])


def test_report_generator_exports_artifacts(tmp_path) -> None:
    generator = ReportGenerator()
    payload = {
        "families": {},
        "summary": {
            "total_controls": 2,
            "passed": 1,
            "failed": 1,
            "compliance_score": 50.0,
            "prioritized_findings": [
                {
                    "family_id": "AC",
                    "control_id": "AC-2",
                    "risk_level": "HIGH",
                    "finding": "Example finding",
                    "recommendations": ["Example recommendation"],
                }
            ],
            "poam_items": [
                {
                    "item_id": "POAM-001",
                    "family_id": "AC",
                    "control_id": "AC-2",
                    "weakness": "Example finding",
                    "risk_level": "HIGH",
                    "recommendations": ["Example recommendation"],
                }
            ],
        },
    }

    artifacts = generator.export_artifacts(payload, output_dir=str(tmp_path), system_name="Test System")

    assert Path(artifacts["report_json"]).exists()
    assert Path(artifacts["poam_json"]).exists()
    assert Path(artifacts["summary_txt"]).exists()
