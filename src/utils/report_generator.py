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
        families = assessment.get("families", {})
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        W = 72  # line width

        def rule(char="═"):
            return char * W

        def section(title):
            return f"\n{rule()}\n  {title}\n{rule()}"

        def wrap(text, indent=4, width=W):
            words = text.split()
            lines_out = []
            cur = " " * indent
            for w in words:
                if len(cur) + len(w) + 1 > width:
                    lines_out.append(cur.rstrip())
                    cur = " " * indent + w + " "
                else:
                    cur += w + " "
            if cur.strip():
                lines_out.append(cur.rstrip())
            return "\n".join(lines_out)

        total = summary.get("total_controls", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        score = summary.get("compliance_score", 0.0)

        lines = [
            rule("═"),
            f"  B.O.B.B.I.E. ASSESSMENT REPORT",
            f"  {system_name}",
            f"  Generated: {now}",
            rule("═"),
            "",
            f"  COMPLIANCE SCORE   {score:.1f}%",
            f"  Total Controls     {total}",
            f"  Passed             {passed}",
            f"  Failed             {failed}",
            "",
        ]

        # ── Per-control breakdown ──────────────────────────────────────────
        lines.append(section("CONTROL RESULTS"))
        for _fid, fdata in families.items():
            for cid, cdata in fdata.get("controls", {}).items():
                status = cdata.get("status", "UNKNOWN").upper()
                risk = cdata.get("risk_level", "")
                status_tag = f"[{status}]" + (f" [{risk}]" if risk and status == "FAIL" else "")
                lines.append(f"\n  {cid}  {status_tag}")

                findings = cdata.get("findings") or []
                recs = cdata.get("recommendations") or []
                narrative = cdata.get("nova_narrative")

                if findings:
                    lines.append("  Findings:")
                    for f in findings:
                        lines.append(wrap(f"• {f}", indent=6))

                if narrative:
                    lines.append("  Nova AI Narrative:")
                    lines.append(wrap(narrative, indent=6))

                if recs:
                    lines.append("  Recommendations:")
                    for r in recs:
                        lines.append(wrap(f"→ {r}", indent=6))

                if status == "PASS" and not findings:
                    lines.append("    All assessment objectives met.")

        # ── Risk summary ───────────────────────────────────────────────────
        risk_counts: dict[str, int] = {}
        for _fid, fdata in families.items():
            for cdata in fdata.get("controls", {}).values():
                if (cdata.get("status") or "").upper() == "FAIL":
                    lvl = cdata.get("risk_level", "UNKNOWN").upper()
                    risk_counts[lvl] = risk_counts.get(lvl, 0) + 1

        if risk_counts:
            lines.append(section("RISK BREAKDOWN  (failed controls)"))
            lines.append("")
            for lvl in ("CRITICAL", "HIGH", "MODERATE", "LOW", "UNKNOWN"):
                if lvl in risk_counts:
                    lines.append(f"  {lvl:<12} {risk_counts[lvl]}")

        lines += ["", rule("═"), ""]
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
