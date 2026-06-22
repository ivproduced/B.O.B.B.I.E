from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils import ReportGenerator
from src.security.input_sanitizer import sanitize_context_keys
from src.security.audit_log import get_default_log

_MAX_SYSTEM_NAME_LEN = 200
_SAFE_NAME_PATTERN = re.compile(r"[^\w\s\-.,():/]")


def _sanitize_system_name(name: str) -> str:
    name = name.strip()[:_MAX_SYSTEM_NAME_LEN]
    return _SAFE_NAME_PATTERN.sub("", name) or "BOBBIE Demo System"


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
        help="Enable LLM narrative generation per control and executive summary",
    )
    parser.add_argument(
        "--apply-nova-suggestions",
        action="store_true",
        help="Apply LLM suggested status/risk automatically when confidence >= threshold",
    )
    parser.add_argument(
        "--nova-confidence-threshold",
        type=float,
        default=0.9,
        help="Confidence threshold (0.0-1.0) required to auto-apply LLM suggestions",
    )
    parser.add_argument(
        "--llm-provider",
        default=None,
        choices=["bedrock", "openai"],
        help="LLM provider to use for narrative generation (default: bedrock). "
             "'openai' supports any OpenAI-compatible endpoint via --llm-base-url.",
    )
    parser.add_argument(
        "--llm-model",
        default=None,
        help="Model ID to use (e.g. gpt-4o, amazon.nova-2-lite-v1:0). "
             "Defaults to the provider's built-in default when not set.",
    )
    parser.add_argument(
        "--llm-base-url",
        default=None,
        help="Base URL for an OpenAI-compatible endpoint "
             "(e.g. http://localhost:11434/v1 for Ollama).",
    )
    parser.add_argument(
        "--llm-api-key",
        default=None,
        help="API key for the LLM provider (falls back to LLM_API_KEY / OPENAI_API_KEY env vars).",
    )

    # ── Infrastructure source options ─────────────────────────────────────────
    parser.add_argument(
        "--infra-source",
        choices=["live", "terraform", "aws-config", "cloudformation"],
        default="live",
        help=(
            "Infrastructure data source for the assessment:\n"
            "  live           – Live boto3 API calls (default, requires active AWS credentials)\n"
            "  terraform      – Parse a local terraform.tfstate file (use with --infra-file)\n"
            "  aws-config     – AWS Config snapshot JSON (local file via --infra-file, or trigger\n"
            "                   delivery to S3 via --config-s3-bucket)\n"
            "  cloudformation – Enumerate deployed CloudFormation/CDK stacks via API"
        ),
    )
    parser.add_argument(
        "--infra-file",
        default=None,
        help=(
            "Path to a local infrastructure file:\n"
            "  terraform  → path/to/terraform.tfstate\n"
            "  aws-config → path/to/config-snapshot.json[.gz]"
        ),
    )
    parser.add_argument(
        "--config-s3-bucket",
        default=None,
        help="S3 bucket where AWS Config delivers snapshots (used with --infra-source aws-config).",
    )
    parser.add_argument(
        "--config-s3-prefix",
        default=None,
        help="S3 key prefix for AWS Config snapshots (optional, used with --config-s3-bucket).",
    )
    parser.add_argument(
        "--cfn-stacks",
        default=None,
        help="Comma-separated CloudFormation stack names/ARNs to include (default: all active stacks).",
    )
    parser.add_argument(
        "--aws-profile",
        default=None,
        help="AWS named profile to use for boto3 sessions (overrides AWS_PROFILE env var).",
    )
    parser.add_argument(
        "--aws-region",
        default="us-east-1",
        help="AWS region for boto3 sessions (default: us-east-1).",
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Only collect the infrastructure snapshot and save it; do not run the assessment.",
    )

    args = parser.parse_args()

    # ── Collect infrastructure snapshot ──────────────────────────────────────
    from src.collectors import collect_infrastructure

    print(f"[BOBBIE] Infrastructure source: {args.infra_source}", flush=True)
    snapshot = collect_infrastructure(
        source=args.infra_source,
        infra_file=args.infra_file,
        config_s3_bucket=args.config_s3_bucket,
        config_s3_prefix=args.config_s3_prefix,
        stack_names=[s.strip() for s in args.cfn_stacks.split(",")] if args.cfn_stacks else None,
        aws_profile=args.aws_profile,
        aws_region=args.aws_region,
    )

    summary = snapshot.to_dict()
    print(f"[BOBBIE] Snapshot: {summary['total_resources']} resources across "
          f"{len(summary['resource_counts'])} types", flush=True)
    if snapshot.errors:
        for err in snapshot.errors:
            print(f"[BOBBIE] WARN: {err}", flush=True)

    # Save snapshot alongside other artifacts
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    snapshot.save(output_path / "infra_snapshot.json")
    print(f"[BOBBIE] Snapshot saved → {output_path / 'infra_snapshot.json'}", flush=True)

    if args.collect_only:
        print(json.dumps(summary, indent=2, default=str))
        return

    from src.config.demo_plan import DEMO_PLAN as demo_plan

    context: dict[str, Any] = {
        "deterministic_run": bool(args.deterministic),
        "nova_narrative": bool(args.nova_narrative),
        "apply_nova_suggestions": bool(args.apply_nova_suggestions),
        "nova_confidence_threshold": float(args.nova_confidence_threshold),
        "llm_provider": args.llm_provider or None,
        "llm_model_id": args.llm_model or None,
        "llm_base_url": args.llm_base_url or None,
        "llm_api_key": args.llm_api_key or None,
        "infra_snapshot": snapshot.resources,
        "infra_source": args.infra_source,
        "aws_region": args.aws_region,
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
        # LLM08/AA02: strip protected keys so a context file cannot override
        # security-critical settings already set by CLI flags.
        safe_external = sanitize_context_keys(external_context)
        stripped = set(external_context) - set(safe_external)
        if stripped:
            print(f"[BOBBIE] SECURITY: stripped protected context keys from context file: {sorted(stripped)}", flush=True)
        context.update(safe_external)

    orchestrator = BOBBIEOrchestrator()
    output = orchestrator.run(demo_plan, context=context)

    report_generator = ReportGenerator()
    safe_system_name = _sanitize_system_name(args.system_name)
    artifacts = report_generator.export_artifacts(
        output,
        output_dir=args.output_dir,
        system_name=safe_system_name,
    )

    # AA06: write the audit log alongside other report artifacts.
    audit_entries = output.get("_audit_log", [])
    if audit_entries:
        audit_path = output_path / "llm_audit_log.json"
        audit_path.write_text(json.dumps(audit_entries, indent=2), encoding="utf-8")
        artifacts["llm_audit_log"] = str(audit_path)
        overrides = sum(1 for e in audit_entries if e.get("event_type") == "NOVA_SUGGESTION_APPLIED")
        blocked = sum(1 for e in audit_entries if e.get("event_type") == "FAIL_TO_PASS_BLOCKED")
        if overrides or blocked:
            print(
                f"[BOBBIE] SECURITY: LLM audit — {overrides} suggestion(s) applied, "
                f"{blocked} FAIL→PASS promotion(s) blocked. See {audit_path}",
                flush=True,
            )

    print(json.dumps(output, indent=2, default=str))
    print(json.dumps({"artifacts": artifacts}, indent=2))


if __name__ == "__main__":
    main()
