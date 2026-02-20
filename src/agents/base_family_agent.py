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
            if (parent / "NIST_SP-800-53_rev5_catalog.json").exists():
                return parent
        return Path.cwd().resolve()

    def load_tagged_catalog(self, context: dict[str, Any]) -> dict[str, Any]:
        repo_root = self.resolve_repo_root(context)
        catalog_path = Path(context.get("catalog_path", repo_root / "NIST_SP-800-53_rev5_catalog.json"))
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
            from src.models.nova_client import create_nova_client

            region = str(context.get("aws_region", "")).strip() or None
            llm = create_nova_client(region_name=region)
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

    def assess_control(self, control_id: str, context: dict[str, Any]) -> dict[str, Any]:
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
