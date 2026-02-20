from __future__ import annotations

from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.tools import evaluate_control_effectiveness_with_objectives


class IAFamilyAgent(BaseFamilyAgent):
    family_id = "IA"
    controls_supported = ["IA-5"]

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if control_id.upper() != "IA-5":
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to IA demo scope"],
                "recommendations": ["Use IA-5 for current IA family demo"],
                "risk_level": "LOW",
                "confidence_score": 1.0,
            }

        catalog = self.load_tagged_catalog(context)
        control = self.find_control(catalog, "ia-5")
        if control is None:
            return {
                "status": "FAIL",
                "findings": ["IA-5 was not found in the OSCAL catalog"],
                "recommendations": ["Validate catalog source and control identifiers"],
                "risk_level": "HIGH",
                "confidence_score": 0.95,
            }

        baselines = control.get("baselines", {})
        included = [name for name, is_member in baselines.items() if is_member]
        findings = []
        if not included:
            findings.append("IA-5 is not mapped to LOW/MODERATE/HIGH/PRIVACY baselines")

        evidence_eval = evaluate_control_effectiveness_with_objectives("IA-5", context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": [
                "Apply password policy checks against IA-5 NIST 800-63B thresholds",
                "Document policy deviations and compensating controls in POA&M output",
            ] + evidence_eval["recommendations"],
            "risk_level": "LOW" if not findings else evidence_eval.get("risk_level", "MEDIUM"),
            "confidence_score": min(0.99, max(0.0, (0.98 + float(evidence_eval.get("confidence_score", 0.9))) / 2)),
            "evidence": {
                "control_id": control.get("id"),
                "title": control.get("title"),
                "baselines": baselines,
                "control_evidence": context.get("control_evidence", {}).get("IA-5", {}),
                "objective_results": evidence_eval.get("objective_results", []),
                "effectiveness": evidence_eval.get("effectiveness", "UNKNOWN"),
            },
        }
