from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.tools import SSMInventoryCollector, evaluate_control_evidence, reconcile_inventory


class CMFamilyAgent(BaseFamilyAgent):
    family_id = "CM"
    controls_supported = ["CM-8"]

    def _build_runtime_context(self, context: dict[str, Any]) -> dict[str, Any]:
        runtime = deepcopy(context)
        control_evidence = dict(runtime.get("control_evidence", {}))
        aws = runtime.get("aws", {}) if isinstance(runtime.get("aws", {}), dict) else {}

        if "CM-8" not in control_evidence and aws.get("ssm"):
            cfg = aws.get("ssm", {})
            expected = list(cfg.get("inventory_expected", cfg.get("mock_inventory", [])))
            discovered = list(cfg.get("inventory_discovered", []))

            collection_error: str | None = None
            if not discovered:
                try:
                    import boto3

                    region = str(cfg.get("region", runtime.get("aws_region", ""))).strip() or None
                    ssm_client = boto3.client("ssm", region_name=region)
                    discovered = SSMInventoryCollector(ssm_client=ssm_client).collect_instance_ids()
                except Exception as exc:
                    collection_error = str(exc)
                    discovered = []

            reconciled = reconcile_inventory(expected=expected, discovered=discovered)
            cm8_evidence: dict[str, Any] = {
                "inventory_expected": reconciled["inventory_expected"],
                "inventory_discovered": reconciled["inventory_discovered"],
                "missing_assets": reconciled["missing_assets"],
                "unmanaged_assets": reconciled["unmanaged_assets"],
            }
            if collection_error:
                cm8_evidence["collection_error"] = collection_error
            control_evidence["CM-8"] = cm8_evidence

        runtime["control_evidence"] = control_evidence
        return runtime

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if control_id.upper() != "CM-8":
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to CM demo scope"],
                "recommendations": ["Use CM-8 for current CM family demo"],
                "risk_level": "LOW",
                "confidence_score": 1.0,
            }

        catalog = self.load_tagged_catalog(context)
        control = self.find_control(catalog, "cm-8")
        if control is None:
            return {
                "status": "FAIL",
                "findings": ["CM-8 was not found in the OSCAL catalog"],
                "recommendations": ["Validate catalog source and control identifiers"],
                "risk_level": "HIGH",
                "confidence_score": 0.95,
            }

        baselines = control.get("baselines", {})
        included = [name for name, is_member in baselines.items() if is_member]
        findings = []
        if not included:
            findings.append("CM-8 is not mapped to LOW/MODERATE/HIGH/PRIVACY baselines")

        runtime_context = self._build_runtime_context(context)
        evidence_eval = evaluate_control_evidence("CM-8", runtime_context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": [
                "Use CM-8 baseline mapping with SSM inventory reconciliation checks",
                "Track inventory deltas and ownership metadata in final control output",
            ] + evidence_eval["recommendations"],
            "risk_level": "LOW" if not findings else evidence_eval.get("risk_level", "MEDIUM"),
            "confidence_score": min(0.99, max(0.0, (0.98 + float(evidence_eval.get("confidence_score", 0.9))) / 2)),
            "evidence": {
                "control_id": control.get("id"),
                "title": control.get("title"),
                "baselines": baselines,
                "control_evidence": runtime_context.get("control_evidence", {}).get("CM-8", {}),
            },
        }
