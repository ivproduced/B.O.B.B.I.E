from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.parsers import EVTXEvidenceCollector
from src.tools import evaluate_control_effectiveness_with_objectives


class AUFamilyAgent(BaseFamilyAgent):
    family_id = "AU"
    controls_supported = ["AU-3"]

    def _build_runtime_context(self, context: dict[str, Any]) -> dict[str, Any]:
        runtime = deepcopy(context)
        control_evidence = dict(runtime.get("control_evidence", {}))

        if "AU-3" not in control_evidence:
            hydrated = EVTXEvidenceCollector().collect_from_context(runtime)
            if hydrated.get("AU-3"):
                control_evidence["AU-3"] = hydrated["AU-3"]

        runtime["control_evidence"] = control_evidence
        return runtime

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if control_id.upper() != "AU-3":
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to AU demo scope"],
                "recommendations": ["Use AU-3 for current AU family demo"],
                "risk_level": "LOW",
                "confidence_score": 1.0,
            }

        catalog = self.load_tagged_catalog(context)
        control = self.find_control(catalog, "au-3")
        if control is None:
            return {
                "status": "FAIL",
                "findings": ["AU-3 was not found in the OSCAL catalog"],
                "recommendations": ["Validate catalog source and control identifiers"],
                "risk_level": "HIGH",
                "confidence_score": 0.95,
            }

        baselines = control.get("baselines", {})
        included = [name for name, is_member in baselines.items() if is_member]
        findings = []
        if not included:
            findings.append("AU-3 is not mapped to LOW/MODERATE/HIGH/PRIVACY baselines")

        runtime_context = self._build_runtime_context(context)
        evidence_eval = evaluate_control_effectiveness_with_objectives("AU-3", runtime_context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": [
                "Apply AU-3 field-completeness checks against EVTX/CloudWatch evidence",
                "Map missing fields to POA&M-ready remediation language",
            ] + evidence_eval["recommendations"],
            "risk_level": "LOW" if not findings else evidence_eval.get("risk_level", "MEDIUM"),
            "confidence_score": min(0.99, max(0.0, (0.98 + float(evidence_eval.get("confidence_score", 0.9))) / 2)),
            "evidence": {
                "control_id": control.get("id"),
                "title": control.get("title"),
                "baselines": baselines,
                "control_evidence": runtime_context.get("control_evidence", {}).get("AU-3", {}),
                "objective_results": evidence_eval.get("objective_results", []),
                "effectiveness": evidence_eval.get("effectiveness", "UNKNOWN"),
            },
        }
