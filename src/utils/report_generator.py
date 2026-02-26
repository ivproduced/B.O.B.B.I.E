from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ReportGenerator:
    def build_assessment_report(self, assessment: dict[str, Any], system_name: str = "BOBBIE Demo System") -> dict[str, Any]:
        return {
            "assessment_date": datetime.now(timezone.utc).isoformat(),
            "system_name": system_name,
            "bobbie_version": "phase3",
            "summary": assessment.get("summary", {}),
            "families": assessment.get("families", {}),
        }

    def build_poam(self, assessment: dict[str, Any], system_name: str = "BOBBIE Demo System") -> dict[str, Any]:
        poam_items = assessment.get("summary", {}).get("poam_items", [])
        # Include explicit OSCAL metadata to indicate OSCAL 1.2.0 compliance
        # Point produced POA&M at the vendored OSCAL metaschema for
        # deterministic, offline validation in CI. Keep oscal_version too.
        return {
            "$schema": "vendor/oscal-metaschema/oscal_poam_schema.json",
            "oscal_version": "1.2.0",
            "plan-of-action-and-milestones": {
                "metadata": {
                    "title": f"POA&M for {system_name}",
                    "last-modified": datetime.now(timezone.utc).isoformat(),
                    "version": "1.2.0",
                },
                "poam-items": poam_items,
            },
        }

    def read_poam(self, file_path: str) -> dict[str, Any]:
        """Read an OSCAL POA&M (JSON) file and normalize to internal structure.

        Returns a dict with keys: 'metadata' and 'poam_items'. Accepts both
        OSCAL-formatted files and the project's earlier minimal POA&M format.
        """
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(file_path)

        raw = json.loads(p.read_text(encoding="utf-8"))

        # OSCAL POA&M canonical form contains 'plan-of-action-and-milestones'
        if "plan-of-action-and-milestones" in raw:
            poam = raw["plan-of-action-and-milestones"]
            metadata = poam.get("metadata", {})
            poam_items = poam.get("poam-items") or poam.get("poam_items") or []
            return {"metadata": metadata, "poam_items": poam_items}

        # Legacy/simple format: assume top-level keys
        if "poam-items" in raw or "poam_items" in raw:
            metadata = raw.get("metadata", {})
            poam_items = raw.get("poam-items") or raw.get("poam_items") or []
            return {"metadata": metadata, "poam_items": poam_items}

        # Unknown format
        raise ValueError("Unrecognized POA&M/OSCAL structure in file: %s" % file_path)

    def build_human_summary(self, assessment: dict[str, Any], system_name: str = "BOBBIE Demo System") -> str:
        summary = assessment.get("summary", {})
        lines = [
            f"System: {system_name}",
            f"Total controls: {summary.get('total_controls', 0)}",
            f"Passed: {summary.get('passed', 0)}",
            f"Failed: {summary.get('failed', 0)}",
            f"Compliance score: {summary.get('compliance_score', 0.0)}%",
            "",
            "Top prioritized findings:",
        ]
        findings = summary.get("prioritized_findings", [])[:10]
        if not findings:
            lines.append("- None")
        else:
            for finding in findings:
                lines.append(
                    f"- [{finding.get('risk_level', 'LOW')}] {finding.get('control_id', 'UNKNOWN')}: {finding.get('finding', '')}"
                )
        return "\n".join(lines)

    def export_artifacts(
        self,
        assessment: dict[str, Any],
        output_dir: str,
        system_name: str = "BOBBIE Demo System",
    ) -> dict[str, str]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        report = self.build_assessment_report(assessment, system_name=system_name)
        poam = self.build_poam(assessment, system_name=system_name)
        summary_text = self.build_human_summary(assessment, system_name=system_name)

        report_path = out_dir / "assessment_report.json"
        poam_path = out_dir / "poam.json"
        summary_path = out_dir / "assessment_summary.txt"

        self.write_json(report, str(report_path))
        self.write_json(poam, str(poam_path))
        summary_path.write_text(summary_text, encoding="utf-8")

        return {
            "report_json": str(report_path),
            "poam_json": str(poam_path),
            "summary_txt": str(summary_path),
        }

    def write_json(self, payload: dict[str, Any], output_path: str) -> None:
        Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
