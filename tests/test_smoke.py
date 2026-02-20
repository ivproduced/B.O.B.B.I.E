from src.agents.orchestrator import BOBBIEOrchestrator


def test_orchestrator_smoke() -> None:
    orchestrator = BOBBIEOrchestrator()
    plan = {"PL": ["PL-2"], "RA": ["RA-5"]}
    result = orchestrator.run(plan)
    assert result["summary"]["total_controls"] == 2
