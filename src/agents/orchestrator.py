from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from typing import Any

from src.agents.family_registry import get_family_agent, validate_plan_vs_registry
from src.agents.base_family_agent import set_llm_budget, _LLM_BUDGET_DEFAULT
from src.security.audit_log import reset_default_log, get_default_log
from src.security.input_sanitizer import sanitize_prompt_field, sanitize_findings_list


@dataclass
class _Task:
    family_id: str
    control_id: str


class BOBBIEOrchestrator:
    @staticmethod
    def _risk_rank(level: str) -> int:
        order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return order.get(str(level).upper(), 0)

    def _build_control_tasks(self, control_plan: dict[str, list[str]], deterministic: bool) -> list[_Task]:
        items: list[_Task] = []
        family_ids = sorted(control_plan.keys()) if deterministic else list(control_plan.keys())
        for family_id in family_ids:
            controls = control_plan.get(family_id, [])
            control_ids = sorted(controls) if deterministic else controls
            for control_id in control_ids:
                items.append(_Task(family_id=family_id, control_id=control_id))
        return items

    def _run_single_control(self, task: _Task, context: dict[str, Any]) -> dict[str, Any]:
        family_agent = get_family_agent(task.family_id)
        return family_agent.assess_control(task.control_id, context)

    def _timeout_result(self, task: _Task, timeout_seconds: float) -> dict[str, Any]:
        return {
            "control_id": task.control_id,
            "status": "FAIL",
            "findings": [f"Control execution timed out after {timeout_seconds:.2f}s"],
            "recommendations": ["Increase timeout or optimize control evidence collection"],
            "risk_level": "HIGH",
            "confidence_score": 1.0,
            "evidence": {"timeout_seconds": timeout_seconds},
        }

    @staticmethod
    def _exception_result(task: _Task, exc: Exception) -> dict[str, Any]:
        return {
            "control_id": task.control_id,
            "status": "FAIL",
            "findings": [f"Control execution failed: {type(exc).__name__}: {exc}"],
            "recommendations": ["Inspect control implementation and evidence inputs for runtime errors"],
            "risk_level": "HIGH",
            "confidence_score": 1.0,
            "evidence": {"error": str(exc)},
        }

    def _build_prioritized_findings(self, family_payload: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = []
        for family_id, payload in family_payload.items():
            controls = payload.get("controls", {})
            for control_id, control_result in controls.items():
                status = str(control_result.get("status", "")).upper()
                if status != "FAIL":
                    continue
                risk_level = str(control_result.get("risk_level", "LOW")).upper()
                for finding in control_result.get("findings", []):
                    findings.append(
                        {
                            "family_id": family_id,
                            "control_id": control_id,
                            "risk_level": risk_level,
                            "finding": str(finding),
                            "recommendations": control_result.get("recommendations", []),
                        }
                    )
        findings.sort(key=lambda item: self._risk_rank(item["risk_level"]), reverse=True)
        return findings

    def _build_poam_items(self, prioritized_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        poam_items: list[dict[str, Any]] = []
        for index, item in enumerate(prioritized_findings, start=1):
            poam_items.append(
                {
                    "item_id": f"POAM-{index:03d}",
                    "family_id": item["family_id"],
                    "control_id": item["control_id"],
                    "weakness": item["finding"],
                    "risk_level": item["risk_level"],
                    "recommendations": item["recommendations"],
                }
            )
        return poam_items

    def _invoke_nova_executive_summary(
        self, summary: dict[str, Any], context: dict[str, Any]
    ) -> str | None:
        """Call Nova Pro for a cross-control compliance executive narrative. Returns None on failure."""
        try:
            from src.models.nova_client import create_nova_client

            region = str(context.get("aws_region", "")).strip() or None
            llm = create_nova_client(region_name=region)
            top_findings = summary.get("prioritized_findings", [])[:5]

            # LLM01/AA01: sanitize finding text before embedding in the prompt.
            findings_lines: list[str] = []
            for f in top_findings:
                safe_risk = sanitize_prompt_field(str(f.get("risk_level", "")), "risk_level", max_len=20)
                safe_ctrl = sanitize_prompt_field(str(f.get("control_id", "")), "control_id", max_len=20)
                safe_finding = sanitize_prompt_field(str(f.get("finding", "")), "finding", max_len=300)
                findings_lines.append(f"- [{safe_risk}] {safe_ctrl}: {safe_finding}")

            findings_text = "\n".join(findings_lines) if findings_lines else "- No failures detected"
            prompt = (
                f"You are a federal security compliance officer.\n"
                f"NIST SP 800-53 assessment results:\n"
                f"- Total controls assessed: {int(summary.get('total_controls', 0))}\n"
                f"- Passed: {int(summary.get('passed', 0))}\n"
                f"- Failed: {int(summary.get('failed', 0))}\n"
                f"- Compliance score: {float(summary.get('compliance_score', 0.0))}%\n\n"
                f"Top priority findings:\n{findings_text}\n\n"
                f"Write a 3-4 sentence executive compliance narrative. "
                f"Summarize the overall security posture, the most critical risks, "
                f"and the immediate recommended actions. Be authoritative and actionable."
            )
            response = llm.invoke(prompt)
            return str(response.content).strip()
        except Exception:
            return None

    def run(self, control_plan: dict[str, list[str]], context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        orchestrator_cfg = context.get("orchestrator", {}) if isinstance(context.get("orchestrator", {}), dict) else {}
        deterministic_mode = bool(context.get("deterministic_run", orchestrator_cfg.get("deterministic_mode", False)))
        control_timeout_seconds = float(orchestrator_cfg.get("control_timeout_seconds", 30.0))

        # LLM04: Reset audit log and initialise per-run LLM call budget before any work.
        audit_log = reset_default_log()
        nova_enabled = bool(context.get("nova_narrative"))
        # Budget: 3 Nova calls per control (narrative + recommendations + suggestion) + 1 executive.
        llm_budget = (len([c for ctrls in control_plan.values() for c in ctrls]) * 3 + 1) if nova_enabled else 0
        llm_budget = min(llm_budget, _LLM_BUDGET_DEFAULT)
        set_llm_budget(llm_budget)

        # Validate plan against declared registry and ensure atomic assignment.
        validate_plan_vs_registry(control_plan)

        # Validation: ensure each control_id is assigned to exactly one family in the provided plan.
        control_to_families: dict[str, list[str]] = {}
        for fam, ctrls in control_plan.items():
            for c in ctrls:
                control_to_families.setdefault(c, []).append(fam)
        duplicates = {c: fs for c, fs in control_to_families.items() if len(fs) > 1}
        if duplicates:
            dup_msgs = [f"{c}: {', '.join(sorted(fs))}" for c, fs in duplicates.items()]
            raise ValueError(
                "Control assignment error: some controls are assigned to multiple families: " + "; ".join(dup_msgs)
            )

        control_tasks = self._build_control_tasks(control_plan, deterministic=deterministic_mode)
        worker_count = int(orchestrator_cfg.get("max_workers", min(8, max(1, len(control_tasks)))))

        output: dict[str, Any] = {"families": {}, "summary": {}}

        family_controls: dict[str, dict[str, Any]] = {family_id: {} for family_id in control_plan}

        with ThreadPoolExecutor(max_workers=max(1, worker_count)) as executor:
            future_map = {
                executor.submit(self._run_single_control, task, context): task
                for task in control_tasks
            }

            for future, task in future_map.items():
                try:
                    result = future.result(timeout=control_timeout_seconds)
                except TimeoutError:
                    result = self._timeout_result(task, timeout_seconds=control_timeout_seconds)
                except Exception as exc:
                    result = self._exception_result(task, exc)

                family_controls.setdefault(task.family_id, {})[task.control_id] = result

        total_controls = 0
        passed_controls = 0

        for family_id in (sorted(control_plan.keys()) if deterministic_mode else control_plan.keys()):
            family_agent = get_family_agent(family_id)
            results = family_controls.get(family_id, {})
            family_result = family_agent.aggregate_family_results(results)
            output["families"][family_id] = {
                "controls": family_result.controls,
                "summary": family_result.summary,
            }
            total_controls += family_result.summary["total_controls"]
            passed_controls += family_result.summary["passed"]

        prioritized_findings = self._build_prioritized_findings(output["families"])
        poam_items = self._build_poam_items(prioritized_findings)

        output["summary"] = {
            "total_controls": total_controls,
            "passed": passed_controls,
            "failed": total_controls - passed_controls,
            "compliance_score": round((passed_controls / total_controls) * 100, 1) if total_controls else 0.0,
            "deterministic_mode": deterministic_mode,
            "prioritized_findings": prioritized_findings,
            "poam_items": poam_items,
        }

        if context.get("nova_narrative"):
            narrative = self._invoke_nova_executive_summary(output["summary"], context)
            if narrative:
                output["summary"]["nova_narrative"] = narrative

        # AA06: attach the audit log to the output so it travels with every report.
        output["_audit_log"] = audit_log.entries()

        return output
