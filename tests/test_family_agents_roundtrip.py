from pathlib import Path

from src.agents.orchestrator import BOBBIEOrchestrator


def test_orchestrator_real_oscal_roundtrip_for_pl_pm() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    result = orchestrator.run(
        control_plan={"PL": ["PL-2"], "PM": ["PM-9"]},
        context={"repo_root": str(root)},
    )

    pl_result = result["families"]["PL"]["controls"]["PL-2"]
    pm_result = result["families"]["PM"]["controls"]["PM-9"]

    assert pl_result["status"] in {"PASS", "FAIL"}
    assert pm_result["status"] in {"PASS", "FAIL"}
    assert "evidence" in pl_result
    assert "evidence" in pm_result
    assert result["summary"]["total_controls"] == 2


def test_orchestrator_real_oscal_roundtrip_for_full_demo_families() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    demo_plan = {
        "PL": ["PL-2"],
        "PM": ["PM-9"],
        "SI": ["SI-4", "SI-2"],
        "CM": ["CM-8"],
        "AC": ["AC-2", "AC-7"],
        "AU": ["AU-3"],
        "IA": ["IA-5"],
        "RA": ["RA-5"],
    }

    result = orchestrator.run(demo_plan, context={"repo_root": str(root)})

    assert result["summary"]["total_controls"] == 10
    for family_id, controls in demo_plan.items():
        for control_id in controls:
            control_result = result["families"][family_id]["controls"][control_id]
            assert control_result["status"] in {"PASS", "FAIL", "NOT_APPLICABLE"}
            assert "evidence" in control_result
