from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.base_family_agent import BaseFamilyAgent
from src.parsers import EVTXEvidenceCollector
from src.tools import evaluate_control_evidence, evaluate_control_effectiveness_with_objectives


class ACFamilyAgent(BaseFamilyAgent):
    family_id = "AC"
    controls_supported = ["AC-2", "AC-7"]

    def _build_runtime_context(self, context: dict[str, Any]) -> dict[str, Any]:
        runtime = deepcopy(context)
        control_evidence = dict(runtime.get("control_evidence", {}))

        if "AC-2" not in control_evidence or "AC-7" not in control_evidence:
            hydrated = EVTXEvidenceCollector().collect_from_context(runtime)
            if "AC-2" not in control_evidence and hydrated.get("AC-2"):
                control_evidence["AC-2"] = hydrated["AC-2"]
            if "AC-7" not in control_evidence and hydrated.get("AC-7"):
                control_evidence["AC-7"] = hydrated["AC-7"]

        runtime["control_evidence"] = control_evidence
        return runtime

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        normalized = control_id.lower()
        if normalized not in {"ac-2", "ac-7"}:
            return {
                "status": "NOT_APPLICABLE",
                "findings": [f"{control_id} is not mapped to AC demo scope"],
                "recommendations": ["Use AC-2 or AC-7 for current AC family demo"],
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

        runtime_context = self._build_runtime_context(context)

        if control_id.upper() == "AC-2":
            evidence_eval = evaluate_control_effectiveness_with_objectives("AC-2", runtime_context)
        else:
            evidence_eval = evaluate_control_evidence(control_id.upper(), runtime_context)
        findings.extend(evidence_eval["findings"])

        return {
            "status": "PASS" if not findings else "FAIL",
            "findings": findings,
            "recommendations": [
                "Use baseline tags with EVTX evidence checks for final AC assessment",
                "Correlate account and lockout events to objective statements",
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
