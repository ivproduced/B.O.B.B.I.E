from __future__ import annotations

from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.tools import evaluate_control_effectiveness_with_objectives


class PLFamilyAgent(BaseFamilyAgent):
    family_id = "PL"
    controls_supported = ["PL-2"]

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if control_id.upper() != "PL-2":
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to PL demo scope"],
                "recommendations": ["Use PL-2 for current PL family demo"],
                "risk_level": "LOW",
                "confidence_score": 1.0,
            }

        catalog = self.load_tagged_catalog(context)

        pl2 = self.find_control(catalog, "pl-2")
        if pl2 is None:
            return {
                "status": "FAIL",
                "findings": ["PL-2 was not found in the OSCAL catalog"],
                "recommendations": ["Validate catalog source and control identifiers"],
                "risk_level": "HIGH",
                "confidence_score": 0.95,
            }

        baseline_membership = pl2.get("baselines", {})
        included = [key for key, value in baseline_membership.items() if value]

        findings: list[str] = []
        if not included:
            findings.append("PL-2 is not included in LOW/MODERATE/HIGH/PRIVACY baseline profiles")

        evidence_eval = evaluate_control_effectiveness_with_objectives("PL-2", context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": [
                "Confirm baseline selection aligns with system impact level",
                "Use baseline tags for family-agent control routing",
            ] + evidence_eval["recommendations"],
            "risk_level": "LOW" if not findings else evidence_eval.get("risk_level", "MEDIUM"),
            "confidence_score": min(0.99, max(0.0, (0.98 + float(evidence_eval.get("confidence_score", 0.9))) / 2)),
            "evidence": {
                "control_id": pl2.get("id"),
                "title": pl2.get("title"),
                "baselines": baseline_membership,
                "control_evidence": context.get("control_evidence", {}).get("PL-2", {}),
                "objective_results": evidence_eval.get("objective_results", []),
                "effectiveness": evidence_eval.get("effectiveness", "UNKNOWN"),
            },
        }
