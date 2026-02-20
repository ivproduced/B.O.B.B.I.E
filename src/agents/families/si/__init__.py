from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.tools import (
    CloudWatchEvidenceCollector,
    NVDKEVEnricher,
    SSMPatchCollector,
    evaluate_control_evidence,
    evaluate_control_effectiveness_with_objectives,
)


class SIFamilyAgent(BaseFamilyAgent):
    family_id = "SI"
    controls_supported = ["SI-2", "SI-4"]

    def _build_runtime_context(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        runtime = deepcopy(context)
        control_evidence = dict(runtime.get("control_evidence", {}))
        aws = runtime.get("aws", {}) if isinstance(runtime.get("aws", {}), dict) else {}

        if control_id.upper() == "SI-4":
            if "SI-4" not in control_evidence and aws.get("cloudwatch"):
                cfg = aws.get("cloudwatch", {})
                log_group = str(cfg.get("log_group", "")).strip()
                hours = int(cfg.get("hours", 24) or 24)
                if log_group:
                    try:
                        import boto3

                        region = str(cfg.get("region", runtime.get("aws_region", ""))).strip() or None
                        logs_client = boto3.client("logs", region_name=region)
                        control_evidence["SI-4"] = CloudWatchEvidenceCollector(logs_client=logs_client).collect(log_group=log_group, hours=hours)
                    except Exception as exc:
                        control_evidence["SI-4"] = {"hourly_event_counts": [], "collection_error": str(exc)}

        if control_id.upper() == "SI-2":
            if "SI-2" not in control_evidence and aws.get("ssm"):
                cfg = aws.get("ssm", {})
                instance_ids = list(cfg.get("instance_ids", []))
                raw_patches = list(cfg.get("patches", []))
                kev_vulns = list(cfg.get("kev_vulnerabilities", []))

                if raw_patches:
                    patches = raw_patches
                elif instance_ids:
                    try:
                        import boto3

                        region = str(cfg.get("region", runtime.get("aws_region", ""))).strip() or None
                        ssm_client = boto3.client("ssm", region_name=region)
                        patch_states = SSMPatchCollector(ssm_client=ssm_client).collect_patch_states(instance_ids)
                        patches = []
                        for state in patch_states:
                            critical_missing = int(state.get("critical_non_compliant_count", 0))
                            high_missing = int(state.get("security_non_compliant_count", 0))
                            for idx in range(critical_missing):
                                patches.append(
                                    {
                                        "cve": f"CRITICAL-PATCH-{idx + 1}",
                                        "severity": "CRITICAL",
                                        "days_open": int(cfg.get("critical_days_open", 30)),
                                        "compensating_control": False,
                                    }
                                )
                            for idx in range(high_missing):
                                patches.append(
                                    {
                                        "cve": f"HIGH-PATCH-{idx + 1}",
                                        "severity": "HIGH",
                                        "days_open": int(cfg.get("high_days_open", 45)),
                                        "compensating_control": False,
                                    }
                                )
                    except Exception as exc:
                        patches = [{"cve": "UNKNOWN", "severity": "HIGH", "days_open": 999, "compensating_control": False, "collection_error": str(exc)}]
                else:
                    patches = []

                enriched = NVDKEVEnricher().enrich(patches, kev_vulns=kev_vulns)
                control_evidence["SI-2"] = {"patches": enriched}

        runtime["control_evidence"] = control_evidence
        return runtime

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        normalized = control_id.lower()
        if normalized not in {"si-2", "si-4"}:
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to SI demo scope"],
                "recommendations": ["Use SI-2 or SI-4 for current SI family demo"],
                "risk_level": "LOW",
                "confidence_score": 1.0,
            }

        catalog = self.load_tagged_catalog(context)
        control = self.find_control(catalog, normalized)
        if control is None:
            return {
                "status": "FAIL",
                "findings": [f"{control_id} was not found in the OSCAL catalog"],
                "recommendations": ["Validate catalog source and control identifiers"],
                "risk_level": "HIGH",
                "confidence_score": 0.95,
            }

        baselines = control.get("baselines", {})
        included = [name for name, is_member in baselines.items() if is_member]
        findings = []
        if not included:
            findings.append(f"{control_id} is not mapped to LOW/MODERATE/HIGH/PRIVACY baselines")

        runtime_context = self._build_runtime_context(control_id, context)

        if control_id.upper() == "SI-2":
            evidence_eval = evaluate_control_effectiveness_with_objectives("SI-2", runtime_context)
        else:
            evidence_eval = evaluate_control_evidence(control_id.upper(), runtime_context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": [
                "Map SI baseline tags to CloudWatch and patch-compliance evidence collection",
                "Prioritize exploitability and SLA breaches in remediation output",
            ] + evidence_eval["recommendations"],
            "risk_level": "LOW" if not findings else evidence_eval.get("risk_level", "MEDIUM"),
            "confidence_score": min(0.99, max(0.0, (0.98 + float(evidence_eval.get("confidence_score", 0.9))) / 2)),
            "evidence": {
                "control_id": control.get("id"),
                "title": control.get("title"),
                "baselines": baselines,
                "control_evidence": runtime_context.get("control_evidence", {}).get(control_id.upper(), {}),
                "objective_results": evidence_eval.get("objective_results", []),
                "effectiveness": evidence_eval.get("effectiveness", "UNKNOWN"),
            },
        }
