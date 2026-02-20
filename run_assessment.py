import argparse

from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils import ReportGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run BOBBIE full assessment plan")
    parser.add_argument("--output-dir", default="artifacts", help="Output directory for report artifacts")
    parser.add_argument("--system-name", default="BOBBIE Demo System", help="System name used in generated reports")
    parser.add_argument("--deterministic", action="store_true", help="Enable deterministic control ordering")
    parser.add_argument("--control-timeout-seconds", type=float, default=30.0, help="Per-control timeout in seconds")
    parser.add_argument("--max-workers", type=int, default=8, help="Maximum concurrent workers")
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

    orchestrator = BOBBIEOrchestrator()
    output = orchestrator.run(
        demo_plan,
        context={
            "deterministic_run": bool(args.deterministic),
            "orchestrator": {
                "control_timeout_seconds": float(args.control_timeout_seconds),
                "max_workers": int(args.max_workers),
                "deterministic_mode": bool(args.deterministic),
            },
        },
    )

    report_generator = ReportGenerator()
    artifacts = report_generator.export_artifacts(
        output,
        output_dir=args.output_dir,
        system_name=args.system_name,
    )

    print(output)
    print({"artifacts": artifacts})


if __name__ == "__main__":
    main()
