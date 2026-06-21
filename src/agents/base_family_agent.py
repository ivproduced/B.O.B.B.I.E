from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.parsers import load_catalog_and_tag_baselines, load_standard_baselines


@dataclass
class FamilyAssessmentResult:
    family_id: str
    controls: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)


class BaseFamilyAgent:
    family_id: str = "UNKNOWN"
    controls_supported: list[str] = []

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        return {"status": "NOT_IMPLEMENTED", "control_id": control_id}

    def resolve_repo_root(self, context: dict[str, Any]) -> Path:
        context_root = context.get("repo_root")
        if context_root:
            return Path(str(context_root)).expanduser().resolve()

        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "data" / "NIST_SP-800-53_rev5_catalog.json").exists():
                return parent
        return Path.cwd().resolve()

    def load_tagged_catalog(self, context: dict[str, Any]) -> dict[str, Any]:
        repo_root = self.resolve_repo_root(context)
        catalog_path = Path(context.get("catalog_path", repo_root / "data" / "NIST_SP-800-53_rev5_catalog.json"))
        baselines = load_standard_baselines(str(repo_root))
        return load_catalog_and_tag_baselines(str(catalog_path), baselines)

    @staticmethod
    def find_control(catalog: dict[str, Any], control_id: str) -> dict[str, Any] | None:
        control_id = control_id.lower()
        for group in catalog.get("catalog", {}).get("groups", []):
            for control in group.get("controls", []):
                if str(control.get("id", "")).lower() == control_id:
                    return control
        for control in catalog.get("catalog", {}).get("controls", []):
            if str(control.get("id", "")).lower() == control_id:
                return control
        return None

    def _invoke_nova_narrative(
        self,
        control_id: str,
        status: str,
        findings: list[str],
        context: dict[str, Any],
    ) -> str | None:
        """Call Nova Pro for a human-readable risk narrative. Returns None on any failure."""
        try:
            from src.models.llm_factory import create_llm_client

            llm = create_llm_client(context)
            findings_text = (
                "\n".join(f"- {f}" for f in findings) if findings else "- No findings"
            )
            prompt = (
                f"You are a federal security compliance analyst assessing NIST SP 800-53.\n"
                f"Control: {control_id.upper()}\n"
                f"Assessment result: {status}\n"
                f"Findings:\n{findings_text}\n\n"
                f"Write a concise 2-3 sentence risk narrative for this control. "
                f"Describe the compliance posture and key risk implications. "
                f"Do not repeat findings verbatim. Be direct and specific."
            )
            response = llm.invoke(prompt)
            return str(response.content).strip()
        except Exception:
            return None

    def _invoke_nova_recommendations(
        self,
        control_id: str,
        findings: list[str],
        context: dict[str, Any],
    ) -> list[str]:
        """Call Nova Pro to generate concise remediation recommendations. Returns empty list on failure."""
        try:
            from src.models.llm_factory import create_llm_client

            llm = create_llm_client(context)
            findings_text = (
                "\n".join(f"- {f}" for f in findings) if findings else "- No findings"
            )
            prompt = (
                f"You are a federal security compliance engineer.\n"
                f"Control: {control_id.upper()}\n"
                f"Context: The deterministic assessment produced a FAIL status with the following findings:\n{findings_text}\n\n"
                f"Provide 3 concise, actionable remediation recommendations aimed at operators or engineers. "
                f"Return each recommendation as a short bullet (one sentence)."
            )
            response = llm.invoke(prompt)
            text = str(response.content).strip()
            # Split into lines and clean bullets
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            recs: list[str] = []
            for ln in lines:
                # remove leading bullet markers
                if ln.startswith("- ") or ln.startswith("* ") or ln.startswith("• "):
                    recs.append(ln[2:].strip())
                else:
                    recs.append(ln)
            # prefer up to 5 recommendations
            return recs[:5]
        except Exception:
            return []

    def _invoke_nova_suggestion(
        self,
        control_id: str,
        status: str,
        findings: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Call Nova to propose a suggested status and risk level with confidence.
        Returns a dict with keys: suggested_status, suggested_risk, confidence, explanation
        or None on failure.
        """
        try:
            from src.models.llm_factory import create_llm_client

            llm = create_llm_client(context)
            findings_text = (
                "\n".join(f"- {f}" for f in findings) if findings else "- No findings"
            )
            prompt = (
                f"You are a senior federal compliance analyst.\n"
                f"Control: {control_id.upper()}\n"
                f"Deterministic assessment result: {status}\n"
                f"Findings:\n{findings_text}\n\n"
                f"Based on the findings, suggest a status (PASS or FAIL) and a risk level (LOW, MEDIUM, HIGH, CRITICAL). "
                f"Return your answer as JSON with keys: suggested_status, suggested_risk, confidence (0.0-1.0), explanation. "
                f"Keep explanation to one sentence."
            )
            response = llm.invoke(prompt)
            text = str(response.content).strip()
            # Try to parse a simple JSON object from the response
            try:
                import json as _json

                parsed = _json.loads(text)
                return {
                    "suggested_status": parsed.get("suggested_status"),
                    "suggested_risk": parsed.get("suggested_risk"),
                    "confidence": float(parsed.get("confidence", 0.0)),
                    "explanation": parsed.get("explanation", ""),
                }
            except Exception:
                # Fallback: attempt to extract tokens heuristically
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                suggestion = {"suggested_status": None, "suggested_risk": None, "confidence": 0.0, "explanation": text}
                for ln in lines:
                    up = ln.upper()
                    if "PASS" in up:
                        suggestion["suggested_status"] = "PASS"
                    if "FAIL" in up:
                        suggestion["suggested_status"] = "FAIL"
                    for lvl in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                        if lvl in up:
                            suggestion["suggested_risk"] = lvl
                return suggestion
        except Exception:
            return None

    def assess_control(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        # Runtime routing check: ensure the control id matches this agent's family prefix.
        fam = (self.family_id or "").upper()
        ctrl = (control_id or "").upper()
        if fam and not ctrl.startswith(fam + "-"):
            return {
                "control_id": control_id,
                "status": "ERROR",
                "findings": [f"Control {control_id} routed to family {self.family_id} which does not own it"],
                "recommendations": [
                    "Verify control routing in the orchestrator: each control must be assessed by its owning family agent"
                ],
                "risk_level": "HIGH",
                "confidence_score": 0.0,
                "evidence": {},
            }

        evidence = self.collect_evidence(control_id, context)
        result: dict[str, Any] = {
            "control_id": control_id,
            "status": evidence.get("status", "NOT_IMPLEMENTED"),
            "findings": evidence.get("findings", []),
            "recommendations": evidence.get("recommendations", []),
            "risk_level": evidence.get("risk_level", "LOW"),
            "confidence_score": evidence.get("confidence_score", 0.0),
            "evidence": evidence.get("evidence", {}),
        }

        if context.get("nova_narrative"):
            narrative = self._invoke_nova_narrative(
                control_id=control_id,
                status=result["status"],
                findings=result["findings"],
                context=context,
            )
            if narrative:
                result["nova_narrative"] = narrative

        # If the control failed and no deterministic recommendations were provided,
        # ask Nova to generate concise remediation steps (operator/engineer focused).
        if (
            str(result.get("status", "")).upper() == "FAIL"
            and not result.get("recommendations")
            and context.get("nova_narrative")
        ):
            recs = self._invoke_nova_recommendations(
                control_id=control_id, findings=result.get("findings", []), context=context
            )
            if recs:
                result["recommendations"] = recs

        # Soft suggestion: ask Nova to propose status/risk and confidence. Do not override
        # unless explicitly enabled via context `apply_nova_suggestions` and confidence >= threshold.
        if context.get("nova_narrative"):
            suggestion = self._invoke_nova_suggestion(
                control_id=control_id, status=result.get("status", ""), findings=result.get("findings", []), context=context
            )
            if suggestion:
                result["nova_suggestion"] = suggestion
                try:
                    apply_flag = bool(context.get("apply_nova_suggestions", False))
                    threshold = float(context.get("nova_confidence_threshold", 0.9))
                    confidence = float(suggestion.get("confidence", 0.0) or 0.0)
                except Exception:
                    apply_flag = False
                    threshold = 0.9
                    confidence = 0.0

                if apply_flag and confidence >= threshold:
                    # record originals for audit
                    result["_original_status"] = result.get("status")
                    result["_original_risk_level"] = result.get("risk_level")
                    if suggestion.get("suggested_status"):
                        result["status"] = suggestion.get("suggested_status")
                    if suggestion.get("suggested_risk"):
                        result["risk_level"] = suggestion.get("suggested_risk")
                    result["nova_suggestion_applied"] = True

        return result

    def aggregate_family_results(self, results: dict[str, Any]) -> FamilyAssessmentResult:
        passed = sum(1 for value in results.values() if value.get("status") == "PASS")
        total = len(results)
        return FamilyAssessmentResult(
            family_id=self.family_id,
            controls=results,
            summary={
                "total_controls": total,
                "passed": passed,
                "failed": total - passed,
            },
        )
