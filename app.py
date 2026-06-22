from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import streamlit as st

from src.agents.orchestrator import BOBBIEOrchestrator
from src.utils import ReportGenerator
from src.security.input_sanitizer import sanitize_context_keys, validate_allowed_path
from src.security.audit_log import get_default_log


REPO_ROOT = Path(__file__).resolve().parent
FROZEN_CONTEXT_PATH = REPO_ROOT / "data" / "demo_frozen" / "demo_context.json"

from src.config.demo_plan import DEMO_PLAN

# Maximum length for the system_name field displayed in reports.
_MAX_SYSTEM_NAME_LEN = 200
_SAFE_NAME_PATTERN = re.compile(r"[^\w\s\-.,():/]")


def _load_uploaded_json(uploaded_file: Any, label: str) -> dict[str, Any] | list[Any] | None:
    if uploaded_file is None:
        return None
    try:
        payload = json.loads(uploaded_file.getvalue().decode("utf-8"))
    except Exception as exc:
        st.error(f"{label} must be valid JSON. Error: {exc}")
        return None
    return payload


def _sanitize_system_name(name: str) -> str:
    """Sanitize system_name to prevent injection into report artifacts."""
    name = name.strip()[:_MAX_SYSTEM_NAME_LEN]
    return _SAFE_NAME_PATTERN.sub("", name) or "BOBBIE Demo System"


def _render_control_table(result: dict[str, Any]) -> None:
    for family_id, family_payload in result.get("families", {}).items():
        with st.expander(f"{family_id} Family"):
            controls = family_payload.get("controls", {})
            for control_id, control_result in controls.items():
                status = control_result.get("status", "UNKNOWN")
                st.markdown(f"### {control_id} — {status}")
                findings = control_result.get("findings", [])
                recommendations = control_result.get("recommendations", [])
                if findings:
                    st.write("Findings:")
                    for finding in findings:
                        st.write(f"- {finding}")
                else:
                    st.write("Findings: none")
                if recommendations:
                    st.write("Recommendations:")
                    for recommendation in recommendations:
                        st.write(f"- {recommendation}")
                nova_narrative = control_result.get("nova_narrative")
                if nova_narrative:
                    st.info(f"**Nova Pro Risk Narrative:** {nova_narrative}")


st.set_page_config(page_title="BOBBIE Assessment Engine", layout="wide")
st.title("BOBBIE: Federal Compliance Assessment")
st.caption("Upload/select data sources, run a deterministic assessment, and download report artifacts.")

with st.sidebar:
    st.header("Assessment Configuration")
    system_name = st.text_input("System Name", value="BOBBIE Demo System")
    deterministic_mode = st.checkbox("Deterministic mode", value=True)
    timeout_seconds = st.number_input("Per-control timeout (seconds)", min_value=1.0, max_value=120.0, value=30.0, step=1.0)
    max_workers = st.number_input("Max workers", min_value=1, max_value=16, value=8, step=1)

    st.subheader("Data Sources")
    use_frozen_context = st.checkbox("Use frozen demo dataset", value=True)
    enable_nova_narrative = st.checkbox(
        "Enable Nova Pro narrative (requires AWS Bedrock)",
        value=True,
        help="Calls Amazon Nova Pro to generate a risk narrative per control and an executive compliance summary.",
    )
    if enable_nova_narrative:
        st.warning(
            "⚠️ **Data Disclosure Notice:** When Nova Pro is enabled, assessment findings "
            "(control IDs, status, and finding text) are transmitted to AWS Bedrock. "
            "Do not enable this feature if findings contain classified or sensitive information "
            "that must not leave your environment. (OWASP LLM06)",
            icon="🔒",
        )
    apply_nova_suggestions = st.checkbox(
        "Apply Nova suggestions automatically",
        value=False,
        help=(
            "If checked, BOBBIE will apply Nova's suggested status/risk when confidence >= threshold. "
            "⚠️ Note: Nova can NEVER automatically promote a FAIL control to PASS — "
            "a human reviewer must approve any such change. (OWASP LLM08/AA02)"
        ),
    )
    nova_confidence_threshold = st.number_input(
        "Nova confidence threshold (0.0-1.0)", min_value=0.0, max_value=1.0, value=0.9, step=0.05
    )
    uploaded_control_evidence = st.file_uploader("Control evidence JSON (optional)", type=["json"])
    uploaded_evtx_payload = st.file_uploader("EVTX payload JSON (optional)", type=["json"])
    uploaded_tickets = st.file_uploader("Approved tickets JSON (optional)", type=["json"])

    catalog_path = st.text_input("Catalog path override (optional)", value="")
    run_assessment = st.button("Run Assessment")


if run_assessment:
    # LLM01: sanitize system_name before it appears in any report artifact.
    safe_system_name = _sanitize_system_name(system_name)

    context: dict[str, Any] = {
        "repo_root": str(REPO_ROOT),
        "deterministic_run": bool(deterministic_mode),
            "nova_narrative": bool(enable_nova_narrative),
            "apply_nova_suggestions": bool(apply_nova_suggestions),
            "nova_confidence_threshold": float(nova_confidence_threshold),
        "orchestrator": {
            "control_timeout_seconds": float(timeout_seconds),
            "max_workers": int(max_workers),
            "deterministic_mode": bool(deterministic_mode),
        },
    }

    # AA03: Validate catalog_path stays within REPO_ROOT before adding to context.
    if catalog_path.strip():
        try:
            safe_catalog = validate_allowed_path(catalog_path.strip(), REPO_ROOT, label="catalog_path")
            context["catalog_path"] = str(safe_catalog)
        except ValueError as path_err:
            st.error(f"Invalid catalog path: {path_err}")
            st.stop()

    if use_frozen_context and FROZEN_CONTEXT_PATH.exists():
        try:
            frozen_payload = json.loads(FROZEN_CONTEXT_PATH.read_text(encoding="utf-8"))
            if isinstance(frozen_payload, dict):
                # LLM08/AA02: strip protected keys from the frozen dataset so it
                # cannot override security-critical settings (e.g. apply_nova_suggestions,
                # nova_confidence_threshold) set by the authenticated UI session.
                safe_frozen = sanitize_context_keys(frozen_payload)
                stripped_keys = set(frozen_payload) - set(safe_frozen)
                for k in stripped_keys:
                    get_default_log().log_context_key_stripped(k)
                context.update(safe_frozen)
        except Exception as exc:
            st.warning(f"Frozen dataset could not be loaded: {exc}")

    control_evidence_payload = _load_uploaded_json(uploaded_control_evidence, "Control evidence")
    if control_evidence_payload is not None:
        if not isinstance(control_evidence_payload, dict):
            st.error("Control evidence JSON must be an object keyed by control ID.")
            st.stop()
        context["control_evidence"] = control_evidence_payload

    evtx_payload = _load_uploaded_json(uploaded_evtx_payload, "EVTX payload")
    if evtx_payload is not None:
        if isinstance(evtx_payload, list):
            context["evtx"] = {"xml_records": evtx_payload}
        elif isinstance(evtx_payload, dict):
            context["evtx"] = evtx_payload
        else:
            st.error("EVTX payload JSON must be a list of XML records or an object.")
            st.stop()

    tickets_payload = _load_uploaded_json(uploaded_tickets, "Approved tickets")
    if tickets_payload is not None:
        if not isinstance(tickets_payload, list):
            st.error("Approved tickets JSON must be a list.")
            st.stop()
        context.setdefault("evtx", {})["approved_tickets"] = tickets_payload

    try:
        orchestrator = BOBBIEOrchestrator()
        result = orchestrator.run(DEMO_PLAN, context=context)
    except Exception as exc:
        st.error(f"Assessment execution failed: {exc}")
        st.stop()

    summary = result.get("summary", {})
    st.subheader("Assessment Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Controls", int(summary.get("total_controls", 0)))
    col2.metric("Passed", int(summary.get("passed", 0)))
    col3.metric("Failed", int(summary.get("failed", 0)))
    col4.metric("Compliance Score", f"{summary.get('compliance_score', 0.0)}%")

    if summary.get("failed", 0) > 0:
        st.warning("Some controls failed. Review findings and recommendations below for remediation.")

    nova_executive = summary.get("nova_narrative")
    if nova_executive:
        st.subheader("Nova Pro Executive Summary")
        st.info(nova_executive)

    st.subheader("Control Results")
    _render_control_table(result)

    report_generator = ReportGenerator()
    report_payload = report_generator.build_assessment_report(result, system_name=safe_system_name)
    poam_payload = report_generator.build_poam(result, system_name=safe_system_name)
    summary_text = report_generator.build_human_summary(result, system_name=safe_system_name)

    st.subheader("Download Artifacts")
    st.download_button(
        "Download Assessment Report JSON",
        data=json.dumps(report_payload, indent=2),
        file_name="assessment_report.json",
        mime="application/json",
    )
    st.download_button(
        "Download POA&M JSON",
        data=json.dumps(poam_payload, indent=2),
        file_name="poam.json",
        mime="application/json",
    )
    st.download_button(
        "Download Human Summary",
        data=summary_text,
        file_name="assessment_summary.txt",
        mime="text/plain",
    )
    # AA06: expose the audit log so reviewers can verify no unexpected LLM overrides occurred.
    audit_entries = result.get("_audit_log", [])
    if audit_entries:
        st.download_button(
            "Download LLM Audit Log JSON",
            data=json.dumps(audit_entries, indent=2),
            file_name="llm_audit_log.json",
            mime="application/json",
            help="Contains a record of every Nova Pro override, blocked FAIL→PASS attempt, and LLM budget event.",
        )
        override_count = sum(1 for e in audit_entries if e.get("event_type") == "NOVA_SUGGESTION_APPLIED")
        blocked_count = sum(1 for e in audit_entries if e.get("event_type") == "FAIL_TO_PASS_BLOCKED")
        if override_count or blocked_count:
            st.warning(
                f"⚠️ **LLM Override Activity:** {override_count} Nova suggestion(s) applied, "
                f"{blocked_count} FAIL→PASS promotion(s) blocked. Download the LLM Audit Log for details.",
                icon="🔍",
            )
