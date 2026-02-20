from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agents.orchestrator import BOBBIEOrchestrator


DEMO_PLAN = {
    "PL": ["PL-2"],
    "PM": ["PM-9"],
    "SI": ["SI-4", "SI-2"],
    "CM": ["CM-8"],
    "AC": ["AC-2", "AC-7"],
    "AU": ["AU-3"],
    "IA": ["IA-5"],
    "RA": ["RA-5"],
}


def main() -> int:
    repo_root = REPO_ROOT
    frozen_dir = repo_root / "data" / "demo_frozen"
    frozen_dir.mkdir(parents=True, exist_ok=True)

    context_path = frozen_dir / "demo_context.json"
    context = json.loads(context_path.read_text(encoding="utf-8")) if context_path.exists() else {}
    context["repo_root"] = str(repo_root)
    context["deterministic_run"] = True
    context["orchestrator"] = {
        "deterministic_mode": True,
        "control_timeout_seconds": 30,
        "max_workers": 4,
    }

    orchestrator = BOBBIEOrchestrator()
    result = orchestrator.run(DEMO_PLAN, context=context)

    (frozen_dir / "expected_assessment_output.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (frozen_dir / "expected_summary.json").write_text(json.dumps(result.get("summary", {}), indent=2), encoding="utf-8")

    print(json.dumps({
        "frozen_dir": str(frozen_dir),
        "expected_assessment_output": str(frozen_dir / "expected_assessment_output.json"),
        "expected_summary": str(frozen_dir / "expected_summary.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
