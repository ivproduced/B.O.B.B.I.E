from __future__ import annotations

from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.tools import evaluate_control_effectiveness_with_objectives


class PMFamilyAgent(BaseFamilyAgent):
    family_id = "PM"
    controls_supported = ["PM-9"]

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if control_id.upper() != "PM-9":
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to PM demo scope"],
                "recommendations": ["Use PM-9 for current PM family demo"],
                "risk_level": "LOW",
                "confidence_score": 1.0,
            }

        catalog = self.load_tagged_catalog(context)

        pm9 = self.find_control(catalog, "pm-9")
        if pm9 is None:
            return {
                "status": "FAIL",
                "findings": ["PM-9 was not found in the OSCAL catalog"],
                "recommendations": ["Validate catalog source and control identifiers"],
                "risk_level": "HIGH",
                "confidence_score": 0.95,
            }

        baseline_membership = pm9.get("baselines", {})
        included = [key for key, value in baseline_membership.items() if value]
        findings: list[str] = []
        recommendations: list[str] = []

        if not included:
            findings.append("PM-9 is not mapped to LOW/MODERATE/HIGH/PRIVACY baseline profiles")
            recommendations.append("Review profile imports and PM family tailoring decisions")
        else:
            recommendations.append("Use PM-9 baseline membership as routing input for risk-register checks")

        evidence_eval = evaluate_control_effectiveness_with_objectives("PM-9", context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": recommendations + evidence_eval["recommendations"],
            "risk_level": "LOW" if not findings else evidence_eval.get("risk_level", "MEDIUM"),
            "confidence_score": min(0.99, max(0.0, (0.98 + float(evidence_eval.get("confidence_score", 0.9))) / 2)),
            "evidence": {
                "control_id": pm9.get("id"),
                "title": pm9.get("title"),
                "baselines": baseline_membership,
                "control_evidence": context.get("control_evidence", {}).get("PM-9", {}),
                "objective_results": evidence_eval.get("objective_results", []),
                "effectiveness": evidence_eval.get("effectiveness", "UNKNOWN"),
            },
        }
