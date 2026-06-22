from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.parsers import load_catalog_and_tag_baselines, load_standard_baselines
from src.security.input_sanitizer import sanitize_prompt_field, sanitize_findings_list, validate_allowed_path
from src.security.output_validator import validate_nova_suggestion
from src.security.audit_log import get_default_log

# Per-assessment LLM call budget enforced across all family agents (LLM04).
# The orchestrator resets _llm_budget_remaining before each run via set_llm_budget().
_LLM_BUDGET_DEFAULT: int = 100  # max Nova invocations per assessment run
_llm_budget_lock = threading.Lock()
_llm_budget_remaining: int = _LLM_BUDGET_DEFAULT  # start at default; orchestrator resets per run


@dataclass
class FamilyAssessmentResult:
    family_id: str
    controls: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)


def _consume_llm_budget(control_id: str) -> bool:
    """Decrement the shared LLM call budget. Returns True if the call is allowed.

    Addresses LLM04 (Model DoS) by capping the total number of Nova invocations
    per assessment run regardless of thread count or control count.
    """
    global _llm_budget_remaining
    with _llm_budget_lock:
        if _llm_budget_remaining <= 0:
            return False
        _llm_budget_remaining -= 1
        return True


def set_llm_budget(budget: int) -> None:
    """Set the per-run LLM call budget. Called by the orchestrator before each run."""
    global _llm_budget_remaining
    with _llm_budget_lock:
        _llm_budget_remaining = max(0, int(budget))


class BaseFamilyAgent:
    family_id: str = "UNKNOWN"
    controls_supported: list[str] = []

    def collect_evidence(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
        return {"status": "NOT_IMPLEMENTED", "control_id": control_id}

    def resolve_repo_root(self, context: dict[str, Any]) -> Path:
        context_root = context.get("repo_root")
        if context_root:
            # Resolve without path traversal validation here – repo_root is
            # set by the app itself (not uploaded data) after context sanitization.
            return Path(str(context_root)).expanduser().resolve()

        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "data" / "NIST_SP-800-53_rev5_catalog.json").exists():
                return parent
        return Path.cwd().resolve()

    def load_tagged_catalog(self, context: dict[str, Any]) -> dict[str, Any]:
        repo_root = self.resolve_repo_root(context)
        default_catalog = repo_root / "data" / "NIST_SP-800-53_rev5_catalog.json"

        raw_catalog_path = context.get("catalog_path", str(default_catalog))
        # AA03: Validate catalog_path is within repo_root to prevent path traversal.
        try:
            catalog_path = validate_allowed_path(raw_catalog_path, repo_root, label="catalog_path")
        except ValueError:
            catalog_path = default_catalog

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
        # LLM04: enforce per-assessment call budget.
        if not _consume_llm_budget(control_id):
            get_default_log().log_llm_budget_exceeded(control_id, _LLM_BUDGET_DEFAULT)
            return None
        try:
            from src.models.llm_factory import create_llm_client

            llm = create_llm_client(context)

            # LLM01/AA01: sanitize all user-controlled fields before prompt embedding.
            safe_control_id = sanitize_prompt_field(control_id.upper(), "control_id", max_len=20)
            safe_status = sanitize_prompt_field(status, "status", max_len=30)
            safe_findings = sanitize_findings_list(findings)
            findings_text = (
                "\n".join(f"- {f}" for f in safe_findings) if safe_findings else "- No findings"
            )
            prompt = (
                f"You are a federal security compliance analyst assessing NIST SP 800-53.\n"
                f"Control: {safe_control_id}\n"
                f"Assessment result: {safe_status}\n"
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
        # LLM04: enforce per-assessment call budget.
        if not _consume_llm_budget(control_id):
            get_default_log().log_llm_budget_exceeded(control_id, _LLM_BUDGET_DEFAULT)
            return []
        try:
            from src.models.llm_factory import create_llm_client

            llm = create_llm_client(context)

            # LLM01/AA01: sanitize all user-controlled fields before prompt embedding.
            safe_control_id = sanitize_prompt_field(control_id.upper(), "control_id", max_len=20)
            safe_findings = sanitize_findings_list(findings)
            findings_text = (
                "\n".join(f"- {f}" for f in safe_findings) if safe_findings else "- No findings"
            )
            prompt = (
                f"You are a federal security compliance engineer.\n"
                f"Control: {safe_control_id}\n"
                f"Context: The deterministic assessment produced a FAIL status with the following findings:\n{findings_text}\n\n"
                f"Provide 3 concise, actionable remediation recommendations aimed at operators or engineers. "
                f"Return each recommendation as a short bullet (one sentence)."
            )
            response = llm.invoke(prompt)
            text = str(response.content).strip()
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            recs: list[str] = []
            for ln in lines:
                if ln.startswith("- ") or ln.startswith("* ") or ln.startswith("• "):
                    recs.append(ln[2:].strip())
                else:
                    recs.append(ln)
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
        Returns a validated dict or None on failure.
        """
        # LLM04: enforce per-assessment call budget.
        if not _consume_llm_budget(control_id):
            get_default_log().log_llm_budget_exceeded(control_id, _LLM_BUDGET_DEFAULT)
            return None
        try:
            from src.models.llm_factory import create_llm_client

            llm = create_llm_client(context)

            # LLM01/AA01: sanitize all user-controlled fields before prompt embedding.
            safe_control_id = sanitize_prompt_field(control_id.upper(), "control_id", max_len=20)
            safe_status = sanitize_prompt_field(status, "status", max_len=30)
            safe_findings = sanitize_findings_list(findings)
            findings_text = (
                "\n".join(f"- {f}" for f in safe_findings) if safe_findings else "- No findings"
            )
            prompt = (
                f"You are a senior federal compliance analyst.\n"
                f"Control: {safe_control_id}\n"
                f"Deterministic assessment result: {safe_status}\n"
                f"Findings:\n{findings_text}\n\n"
                f"Based on the findings, suggest a status (PASS or FAIL) and a risk level (LOW, MEDIUM, HIGH, CRITICAL). "
                f"Return your answer as JSON with keys: suggested_status, suggested_risk, confidence (0.0-1.0), explanation. "
                f"Keep explanation to one sentence."
            )
            response = llm.invoke(prompt)
            text = str(response.content).strip()
            try:
                import json as _json

                parsed = _json.loads(text)
                raw_suggestion = {
                    "suggested_status": parsed.get("suggested_status"),
                    "suggested_risk": parsed.get("suggested_risk"),
                    "confidence": parsed.get("confidence", 0.0),
                    "explanation": parsed.get("explanation", ""),
                }
            except Exception:
                # Fallback: attempt to extract tokens heuristically.
                lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                raw_suggestion: dict[str, Any] = {
                    "suggested_status": None,
                    "suggested_risk": None,
                    "confidence": 0.0,
                    "explanation": text[:500],  # cap heuristic explanation length
                }
                for ln in lines:
                    up = ln.upper()
                    if "PASS" in up:
                        raw_suggestion["suggested_status"] = "PASS"
                    if "FAIL" in up:
                        raw_suggestion["suggested_status"] = "FAIL"
                    for lvl in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                        if lvl in up:
                            raw_suggestion["suggested_risk"] = lvl

            # LLM02/AA05/AA02: validate and sanitize the LLM output before returning.
            return validate_nova_suggestion(raw_suggestion, current_status=status)
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
                    status_changed = False
                    risk_changed = False
                    if suggestion.get("suggested_status"):
                        result["status"] = suggestion.get("suggested_status")
                        status_changed = True
                    if suggestion.get("suggested_risk"):
                        result["risk_level"] = suggestion.get("suggested_risk")
                        risk_changed = True
                    if status_changed or risk_changed:
                        result["nova_suggestion_applied"] = True
                        # AA06: log the override to the audit trail.
                        get_default_log().log_nova_suggestion_applied(
                            control_id=control_id,
                            original_status=str(result["_original_status"]),
                            new_status=result.get("status"),
                            original_risk=str(result["_original_risk_level"]),
                            new_risk=result.get("risk_level"),
                            confidence=confidence,
                            explanation=str(suggestion.get("explanation", "")),
                        )

                # AA06: log any blocked FAIL→PASS attempts regardless of apply_flag.
                if suggestion.get("_fail_to_pass_blocked"):
                    get_default_log().log_fail_to_pass_blocked(
                        control_id=control_id,
                        confidence=confidence,
                        explanation=str(suggestion.get("explanation", "")),
                    )

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
