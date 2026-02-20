from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils import ReportGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BOBBIE full assessment plan")
    parser.add_argument("--output-dir", default="artifacts", help="Output directory for report artifacts")
    parser.add_argument("--system-name", default="BOBBIE Demo System", help="System name used in generated reports")
    parser.add_argument("--deterministic", action="store_true", help="Enable deterministic control ordering")
    parser.add_argument("--control-timeout-seconds", type=float, default=30.0, help="Per-control timeout in seconds")
    parser.add_argument("--max-workers", type=int, default=8, help="Maximum concurrent workers")
    parser.add_argument(
        "--context-file",
        default=None,
        help="Path to a JSON file containing assessment context (control_evidence, evtx, aws, etc.)",
    )
    parser.add_argument(
        "--nova-narrative",
        action="store_true",
        help="Enable Amazon Nova Pro narrative generation per control and executive summary (requires AWS Bedrock)",
    )
    args = parser.parse_args()

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

    context: dict[str, Any] = {
        "deterministic_run": bool(args.deterministic),
        "nova_narrative": bool(args.nova_narrative),
        "orchestrator": {
            "control_timeout_seconds": float(args.control_timeout_seconds),
            "max_workers": int(args.max_workers),
            "deterministic_mode": bool(args.deterministic),
        },
    }

    if args.context_file:
        context_path = Path(args.context_file)
        if not context_path.exists():
            print(f"ERROR: context file not found: {context_path}")
            raise SystemExit(1)
        external_context = json.loads(context_path.read_text(encoding="utf-8"))
        if not isinstance(external_context, dict):
            print("ERROR: context file must contain a JSON object")
            raise SystemExit(1)
        context.update(external_context)

    orchestrator = BOBBIEOrchestrator()
    output = orchestrator.run(demo_plan, context=context)

    report_generator = ReportGenerator()
    artifacts = report_generator.export_artifacts(
        output,
        output_dir=args.output_dir,
        system_name=args.system_name,
    )

    print(json.dumps(output, indent=2, default=str))
    print(json.dumps({"artifacts": artifacts}, indent=2))


if __name__ == "__main__":
    main()
