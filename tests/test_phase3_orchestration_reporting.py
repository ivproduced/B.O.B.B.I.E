from __future__ import annotations

import time
from pathlib import Path

import src.agents.orchestrator as orchestrator_module
from src.agents.base_family_agent import set_llm_budget
from src.agents.orchestrator import BOBBIEOrchestrator
from src.security.audit_log import get_default_log
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


def test_orchestrator_preserves_pre_run_audit_entries() -> None:
    orchestrator = BOBBIEOrchestrator()
    pre_run_entry = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "event_type": "PROTECTED_CONTEXT_KEY_STRIPPED",
        "key": "nova_narrative",
        "reason": "Uploaded data attempted to override a protected security context key (LLM08/AA02).",
    }

    result = orchestrator.run(
        {"PL": ["PL-2"]},
        context={"deterministic_run": True},
        pre_run_audit_entries=[pre_run_entry],
    )

    assert result["_audit_log"][0] == pre_run_entry


def test_executive_summary_skips_when_budget_exhausted(monkeypatch) -> None:
    calls = {"invoke": 0}

    class _Client:
        def invoke(self, prompt: str):
            calls["invoke"] += 1
            return type("Response", (), {"content": "Executive summary"})()

    monkeypatch.setattr("src.models.llm_factory.create_llm_client", lambda context=None: _Client())

    set_llm_budget(0)
    narrative = BOBBIEOrchestrator()._invoke_nova_executive_summary({"prioritized_findings": []}, context={})

    assert narrative is None
    assert calls["invoke"] == 0
    assert any(
        entry.get("event_type") == "LLM_BUDGET_EXCEEDED"
        and entry.get("control_id") == "__executive_summary__"
        for entry in get_default_log().entries()
    )


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
