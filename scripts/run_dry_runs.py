from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils import ReportGenerator


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
    artifacts_root = repo_root / "artifacts" / "dry_runs"
    artifacts_root.mkdir(parents=True, exist_ok=True)

    frozen_context_path = repo_root / "data" / "demo_frozen" / "demo_context.json"
    context = json.loads(frozen_context_path.read_text(encoding="utf-8")) if frozen_context_path.exists() else {}
    context["repo_root"] = str(repo_root)
    context["deterministic_run"] = True
    context["orchestrator"] = {
        "deterministic_mode": True,
        "control_timeout_seconds": 30,
        "max_workers": 4,
    }

    orchestrator = BOBBIEOrchestrator()
    reporter = ReportGenerator()

    run_summaries = []
    known_issues: list[str] = []

    for index in range(1, 4):
        result = orchestrator.run(DEMO_PLAN, context=context)
        run_dir = artifacts_root / f"run_{index}"
        run_dir.mkdir(parents=True, exist_ok=True)
        reporter.export_artifacts(result, output_dir=str(run_dir), system_name=f"BOBBIE Dry Run {index}")

        summary = result.get("summary", {})
        run_summaries.append({"run": index, **summary})

        failed = int(summary.get("failed", 0))
        if failed > 0:
            known_issues.append(f"Run {index}: {failed} failed controls; investigate prioritized findings in run_{index}/assessment_summary.txt")

    if not known_issues:
        known_issues.append("No blocking issues observed across 3 dry runs.")

    report_lines = [
        "# Dry Run Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Run Summaries",
    ]

    for run in run_summaries:
        report_lines.extend(
            [
                f"- Run {run.get('run')}: total={run.get('total_controls', 0)}, passed={run.get('passed', 0)}, failed={run.get('failed', 0)}, compliance={run.get('compliance_score', 0.0)}%",
            ]
        )

    report_lines.extend(
        [
            "",
            "## Known Issues + Fixes",
        ]
    )

    for issue in known_issues:
        report_lines.append(f"- {issue}")

    report_path = artifacts_root / "dry_run_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "artifacts_root": str(artifacts_root),
                "dry_run_report": str(report_path),
                "runs": run_summaries,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
