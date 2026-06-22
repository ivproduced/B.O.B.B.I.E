from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.oscal_catalog import Catalog
from src.security.input_sanitizer import validate_allowed_path
from src.security.audit_log import get_default_log


def _result(findings: list[str], recommendations: list[str], risk_level: str, confidence: float = 0.9) -> dict[str, Any]:
    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "recommendations": recommendations,
        "risk_level": risk_level if findings else "LOW",
        "confidence_score": confidence,
    }


def evaluate_control_evidence(control_id: str, context: dict[str, Any]) -> dict[str, Any]:
    control_key = control_id.upper()
    evidence = context.get("control_evidence", {}).get(control_key)

    if evidence is None:
        return _result(
            findings=[f"No evidence provided for {control_key}"],
            recommendations=[f"Provide control_evidence['{control_key}'] with required fields"],
            risk_level="HIGH",
            confidence=1.0,
        )

    checks: dict[str, Any] = {
        "PL-2": _check_pl2,
        "PM-9": _check_pm9,
        "AC-2": _check_ac2,
        "AC-7": _check_ac7,
        "AU-3": _check_au3,
        "CM-8": _check_cm8,
        "IA-5": _check_ia5,
        "RA-5": _check_ra5,
        "SI-2": _check_si2,
        "SI-4": _check_si4,
    }

    checker = checks.get(control_key)
    if checker is None:
        return _result([], ["No evidence checker configured"], "LOW", confidence=0.6)

    return checker(evidence)


def evaluate_control_effectiveness_with_objectives(control_id: str, context: dict[str, Any]) -> dict[str, Any]:
    control_key = control_id.upper()
    objective_results: list[dict[str, Any]] = []

    if control_key == "AC-2":
        objective_results = _evaluate_ac2_objectives(context)
    elif control_key == "AU-3":
        objective_results = _evaluate_au3_objectives(context)
    elif control_key == "PL-2":
        objective_results = _evaluate_pl2_objectives(context)
    elif control_key == "PM-9":
        objective_results = _evaluate_pm9_objectives(context)
    elif control_key == "IA-5":
        objective_results = _evaluate_ia5_objectives(context)
    elif control_key == "RA-5":
        objective_results = _evaluate_ra5_objectives(context)
    elif control_key == "SI-2":
        objective_results = _evaluate_si2_objectives(context)

    if not objective_results:
        fallback = evaluate_control_evidence(control_key, context)
        fallback["objective_results"] = []
        fallback["effectiveness"] = "EFFECTIVE" if fallback.get("status") == "PASS" else "INEFFECTIVE"
        return fallback

    unmet = [item for item in objective_results if not item["met"]]
    findings = [f"Objective {item['objective_id']} NOT MET: {item['reason']}" for item in unmet]
    recommendations = [
        "Address unmet assessment objectives before declaring control effective",
        "Attach traceable evidence for each 800-53A objective",
    ]

    base = _result(findings, recommendations, risk_level="HIGH" if unmet else "LOW", confidence=0.95)
    base["objective_results"] = objective_results
    base["effectiveness"] = "EFFECTIVE" if not unmet else "INEFFECTIVE"
    return base


def get_control_assessment_objectives(control_id: str, context: dict[str, Any]) -> list[dict[str, str]]:
    repo_root = Path(str(context.get("repo_root", Path.cwd()))).resolve()

    raw_fixture_path = context.get(
        "objective_fixture_path",
        repo_root / "data" / "oscal_samples" / f"objectives_{control_id.lower().replace('-', '')}.json",
    )
    # AA03: Validate that fixture_path stays within repo_root.
    try:
        fixture_path = validate_allowed_path(raw_fixture_path, repo_root, label="objective_fixture_path")
    except ValueError:
        get_default_log().log_path_traversal_blocked(
            label="objective_fixture_path",
            candidate=str(raw_fixture_path),
            allowed_root=str(repo_root),
        )
        fixture_path = repo_root / "data" / "oscal_samples" / f"objectives_{control_id.lower().replace('-', '')}.json"

    if fixture_path.exists():
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        objectives = payload.get("objectives", [])
        if isinstance(objectives, list) and objectives:
            return [
                {
                    "objective_id": str(item.get("objective_id", "unknown-objective-id")),
                    "objective_prose": str(item.get("objective_prose", "")),
                }
                for item in objectives
                if isinstance(item, dict)
            ]

    raw_catalog_path = context.get("catalog_path", repo_root / "data" / "NIST_SP-800-53_rev5_catalog.json")
    # AA03: Validate catalog_path is within repo_root.
    try:
        catalog_path = validate_allowed_path(raw_catalog_path, repo_root, label="catalog_path")
    except ValueError:
        get_default_log().log_path_traversal_blocked(
            label="catalog_path",
            candidate=str(raw_catalog_path),
            allowed_root=str(repo_root),
        )
        catalog_path = repo_root / "data" / "NIST_SP-800-53_rev5_catalog.json"
    if not catalog_path.exists():
        return []

    catalog = Catalog.from_dict(json.loads(catalog_path.read_text(encoding="utf-8")))
    target = control_id.lower()
    control = next((item for item in catalog.controls if item.id == target), None)
    if control is None:
        return []

    return [
        {
            "objective_id": item.id or "unknown-objective-id",
            "objective_prose": item.prose or "",
        }
        for item in control.flat_assessment_objectives
    ]


def _evaluate_ac2_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("AC-2", context)
    evidence = context.get("control_evidence", {}).get("AC-2", {})
    account_events = evidence.get("account_events", [])
    approved_tickets = evidence.get("approved_tickets", [])
    lockouts = evidence.get("lockouts", [])

    tickets_by_account = {
        str(ticket.get("account_id", "")).lower(): bool(ticket.get("isso_approved", False))
        for ticket in approved_tickets
    }
    accounts_with_events = [str(item.get("account_id", "")).lower() for item in account_events if str(item.get("account_id", "")).strip()]

    results: list[dict[str, Any]] = []
    for objective in objective_defs:
        oid = objective["objective_id"].lower()
        prose = objective.get("objective_prose", "")
        prose_lower = prose.lower()

        if any(token in oid or token in prose_lower for token in [".a", "assign", "define", "establish"]):
            met = len(accounts_with_events) > 0
            reason = "Account lifecycle evidence present" if met else "No account lifecycle evidence found"
        elif any(token in oid or token in prose_lower for token in [".b", "approve", "authorization", "authoriz"]):
            unmet_accounts = [account for account in accounts_with_events if not tickets_by_account.get(account, False)]
            met = len(unmet_accounts) == 0 and len(accounts_with_events) > 0
            reason = "All account events mapped to approved tickets" if met else "One or more account events lack approved tickets"
        elif any(token in oid or token in prose_lower for token in [".c", "disable", "remove", "notify", "review", "monitor"]):
            met = bool(lockouts or evidence.get("status_change_notifications") or evidence.get("account_reviews"))
            reason = "Lifecycle enforcement evidence present" if met else "No lifecycle enforcement evidence found"
        else:
            met = len(accounts_with_events) > 0
            reason = "Generic objective inference from available account evidence" if met else "Insufficient evidence for objective"

        results.append(
            {
                "objective_id": objective["objective_id"],
                "met": met,
                "reason": reason,
            }
        )

    if not results:
        results.append(
            {
                "objective_id": "ac-2_obj.unknown",
                "met": False,
                "reason": "No AC-2 assessment objectives were parsed from catalog",
            }
        )

    return results


def _evaluate_au3_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("AU-3", context)
    evidence = context.get("control_evidence", {}).get("AU-3", {})
    records = evidence.get("records", [])
    required = {"timestamp", "event_type", "subject", "outcome", "source_ip"}

    completeness = 0.0
    if records:
        complete_count = 0
        for record in records:
            if all(str(record.get(field, "")).strip() for field in required):
                complete_count += 1
        completeness = complete_count / len(records)

    pii_detections = int(evidence.get("pii_detections", 0))

    results: list[dict[str, Any]] = []
    has_sensitive_objective = False
    for objective in objective_defs:
        oid = objective["objective_id"]
        prose = objective.get("objective_prose", "")
        prose_lower = prose.lower()

        if any(token in prose_lower for token in ["content", "contains", "include", "record"]):
            met = completeness >= 0.95
            reason = (
                f"Required fields completeness {round(completeness * 100, 1)}%"
                if not met
                else "Audit records include required AU-3 content"
            )
        elif any(token in prose_lower for token in ["association", "trace", "identity", "subject"]):
            met = completeness >= 0.95
            reason = "Subject identity traceability verified" if met else "Subject identity traceability incomplete"
        elif any(token in prose_lower for token in ["protect", "sensitive", "privacy", "pii"]):
            has_sensitive_objective = True
            met = pii_detections == 0
            reason = "No sensitive data leakage detected" if met else f"Detected {pii_detections} PII leakage events"
        else:
            met = bool(records)
            reason = "Audit evidence provided" if met else "No audit evidence provided"

        results.append({"objective_id": oid, "met": met, "reason": reason})

    if pii_detections > 0 and not has_sensitive_objective:
        results.append(
            {
                "objective_id": "au-3_obj.sensitive-data",
                "met": False,
                "reason": f"Detected {pii_detections} potential sensitive-data patterns in audit payloads",
            }
        )

    if not results:
        results.append({"objective_id": "au-3_obj.unknown", "met": False, "reason": "No AU-3 assessment objectives were parsed from catalog"})

    return results


def _evaluate_si2_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("SI-2", context)
    evidence = context.get("control_evidence", {}).get("SI-2", {})
    patches = evidence.get("patches", [])

    critical_overdue = 0
    high_overdue = 0
    missing_comp = 0
    for patch in patches:
        severity = str(patch.get("severity", "")).upper()
        days_open = int(patch.get("days_open", 0))
        compensating = bool(patch.get("compensating_control", False))
        if severity == "CRITICAL" and days_open > 15:
            critical_overdue += 1
            if not compensating:
                missing_comp += 1
        elif severity == "HIGH" and days_open > 30:
            high_overdue += 1
            if not compensating:
                missing_comp += 1

    results: list[dict[str, Any]] = []
    for objective in objective_defs:
        oid = objective["objective_id"]
        prose = objective.get("objective_prose", "")
        prose_lower = prose.lower()

        if any(token in prose_lower for token in ["identify", "flaw", "track", "remediate"]):
            met = bool(patches)
            reason = "Patch/flaw inventory evidence present" if met else "No patch/flaw evidence provided"
        elif any(token in prose_lower for token in ["install", "apply", "update", "corrective action"]):
            met = (critical_overdue + high_overdue) == 0
            reason = "Patches applied within SLA" if met else f"Overdue patches found: critical={critical_overdue}, high={high_overdue}"
        elif any(token in prose_lower for token in ["compensating", "mitigation", "document"]):
            met = missing_comp == 0
            reason = "Compensating controls documented where needed" if met else f"{missing_comp} overdue patches missing compensating controls"
        else:
            met = bool(patches)
            reason = "Flaw remediation evidence provided" if met else "No flaw remediation evidence provided"

        results.append({"objective_id": oid, "met": met, "reason": reason})

    if not results:
        results.append({"objective_id": "si-2_obj.unknown", "met": False, "reason": "No SI-2 assessment objectives were parsed from catalog"})

    return results


def _evaluate_ia5_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("IA-5", context)
    evidence = context.get("control_evidence", {}).get("IA-5", {})
    policy = evidence.get("policy", {})

    min_length_ok = int(policy.get("MinimumLength", 0)) >= 14
    complexity_ok = bool(policy.get("ComplexityEnabled", False))
    history_ok = int(policy.get("PasswordHistory", 0)) >= 24
    max_age_ok = int(policy.get("MaximumAge", 999)) <= 60
    weak_algorithms = [str(item).upper() for item in evidence.get("weak_algorithms", [])]
    weak_algo_ok = not any(name in {"DES", "MD5"} for name in weak_algorithms)

    results: list[dict[str, Any]] = []
    for objective in objective_defs:
        oid = objective["objective_id"]
        prose_lower = objective.get("objective_prose", "").lower()

        if any(token in prose_lower for token in ["password", "authenticator", "length", "complexity", "history", "age"]):
            met = min_length_ok and complexity_ok and history_ok and max_age_ok
            reason = "Policy meets IA-5 thresholds" if met else "Policy thresholds not met (length/complexity/history/max age)"
        elif any(token in prose_lower for token in ["protect", "crypt", "algorithm", "hash"]):
            met = weak_algo_ok
            reason = "No weak algorithms detected" if met else f"Weak algorithms present: {', '.join(weak_algorithms)}"
        else:
            met = bool(policy)
            reason = "Policy evidence provided" if met else "No IA-5 policy evidence provided"

        results.append({"objective_id": oid, "met": met, "reason": reason})

    if not results:
        results.append({"objective_id": "ia-5_obj.unknown", "met": False, "reason": "No IA-5 assessment objectives were parsed from catalog"})

    return results


def _evaluate_ra5_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("RA-5", context)
    evidence = context.get("control_evidence", {}).get("RA-5", {})
    vulnerabilities = evidence.get("vulnerabilities", [])

    overdue = 0
    kev_hits = 0
    coverage = float(evidence.get("scan_coverage", 0.0))
    scan_age_hours = float(evidence.get("scan_age_hours", 9999))

    for vuln in vulnerabilities:
        cvss = float(vuln.get("cvss_score", 0))
        days_open = int(vuln.get("days_open", 0))
        if vuln.get("in_kev", False):
            kev_hits += 1
        if cvss >= 9.0 and days_open > 15:
            overdue += 1
        elif cvss >= 7.0 and days_open > 30:
            overdue += 1
        elif cvss >= 4.0 and days_open > 90:
            overdue += 1

    results: list[dict[str, Any]] = []
    for objective in objective_defs:
        oid = objective["objective_id"]
        prose_lower = objective.get("objective_prose", "").lower()

        if any(token in prose_lower for token in ["scan", "vulnerability", "identify", "monitor"]):
            met = bool(vulnerabilities) and scan_age_hours <= 72
            reason = "Recent vulnerability scan evidence present" if met else "Missing or stale vulnerability scan evidence"
        elif any(token in prose_lower for token in ["remediate", "correct", "address", "timeframe", "sla"]):
            met = overdue == 0
            reason = "All vulnerabilities within SLA" if met else f"{overdue} vulnerabilities exceed SLA"
        elif any(token in prose_lower for token in ["known exploited", "kev", "exploit"]):
            met = kev_hits == 0
            reason = "No KEV-matched vulnerabilities open" if met else f"{kev_hits} KEV vulnerabilities require priority remediation"
        elif any(token in prose_lower for token in ["coverage", "asset", "scope"]):
            met = coverage >= 0.95
            reason = "Asset scan coverage acceptable" if met else f"Asset scan coverage too low: {round(coverage * 100, 1)}%"
        else:
            met = bool(vulnerabilities)
            reason = "Vulnerability evidence provided" if met else "No vulnerability evidence provided"

        results.append({"objective_id": oid, "met": met, "reason": reason})

    if not results:
        results.append({"objective_id": "ra-5_obj.unknown", "met": False, "reason": "No RA-5 assessment objectives were parsed from catalog"})

    return results


def _evaluate_pl2_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("PL-2", context)
    evidence = context.get("control_evidence", {}).get("PL-2", {})

    sections_present = set(str(item).lower() for item in evidence.get("sections_present", []))
    required_sections = {"system-characteristics", "control-implementation", "system-implementation", "metadata"}
    missing_sections = required_sections - sections_present
    missing_baseline_controls = int(evidence.get("missing_baseline_controls", 0))
    stale_signatures = int(evidence.get("stale_approvals", 0))

    results: list[dict[str, Any]] = []
    for objective in objective_defs:
        oid = objective["objective_id"]
        prose_lower = objective.get("objective_prose", "").lower()

        if any(token in prose_lower for token in ["plan", "document", "describe", "define"]):
            met = len(missing_sections) == 0
            reason = "Required SSP sections are present" if met else f"Missing SSP sections: {', '.join(sorted(missing_sections))}"
        elif any(token in prose_lower for token in ["implement", "baseline", "control"]):
            met = missing_baseline_controls == 0
            reason = "All baseline controls have implementation statements" if met else f"Missing implementation for {missing_baseline_controls} baseline controls"
        elif any(token in prose_lower for token in ["approve", "review", "authoriz", "signature"]):
            met = stale_signatures == 0
            reason = "Approvals are current" if met else f"{stale_signatures} stale or missing approval signatures"
        else:
            met = len(missing_sections) == 0 and missing_baseline_controls == 0
            reason = "SSP evidence is complete" if met else "SSP evidence incomplete for objective"

        results.append({"objective_id": oid, "met": met, "reason": reason})

    if not results:
        results.append({"objective_id": "pl-2_obj.unknown", "met": False, "reason": "No PL-2 assessment objectives were parsed from catalog"})

    return results


def _evaluate_pm9_objectives(context: dict[str, Any]) -> list[dict[str, Any]]:
    objective_defs = get_control_assessment_objectives("PM-9", context)
    evidence = context.get("control_evidence", {}).get("PM-9", {})
    risks = evidence.get("risks", [])

    invalid_scoring = 0
    missing_mitigation = 0
    missing_approval = 0
    for risk in risks:
        likelihood = float(risk.get("likelihood", 0))
        impact = float(risk.get("impact", 0))
        score = float(risk.get("score", 0))
        approved = bool(risk.get("approved", False))
        mitigation = str(risk.get("mitigation", "")).strip()

        if abs((likelihood * impact) - score) > 0.01:
            invalid_scoring += 1
        if score >= 9 and not mitigation:
            missing_mitigation += 1
        if score >= 6 and not approved:
            missing_approval += 1

    results: list[dict[str, Any]] = []
    for objective in objective_defs:
        oid = objective["objective_id"]
        prose_lower = objective.get("objective_prose", "").lower()

        if any(token in prose_lower for token in ["identify", "analyze", "assess", "risk"]):
            met = bool(risks) and invalid_scoring == 0
            reason = "Risk assessment inventory and scoring are valid" if met else "Risk evidence missing or invalid risk scoring detected"
        elif any(token in prose_lower for token in ["mitigate", "response", "treatment"]):
            met = missing_mitigation == 0
            reason = "High risks include mitigation plans" if met else f"{missing_mitigation} high risks missing mitigation plans"
        elif any(token in prose_lower for token in ["approve", "accept", "authoriz"]):
            met = missing_approval == 0
            reason = "Moderate/high risks have approvals" if met else f"{missing_approval} moderate/high risks missing approvals"
        else:
            met = bool(risks)
            reason = "Risk register evidence provided" if met else "No risk register evidence provided"

        results.append({"objective_id": oid, "met": met, "reason": reason})

    if not results:
        results.append({"objective_id": "pm-9_obj.unknown", "met": False, "reason": "No PM-9 assessment objectives were parsed from catalog"})

    return results


def _check_pl2(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    required_sections = {"system-characteristics", "control-implementation", "system-implementation", "metadata"}
    sections_present = set(evidence.get("sections_present", []))
    missing_sections = sorted(required_sections - sections_present)
    missing_controls = int(evidence.get("missing_baseline_controls", 0))

    if missing_sections:
        findings.append(f"Missing required SSP sections: {', '.join(missing_sections)}")
    if missing_controls > 0:
        findings.append(f"Missing implementation statements for {missing_controls} baseline controls")

    return _result(
        findings,
        ["Complete required OSCAL SSP sections", "Add implementation narratives for all baseline controls"],
        "MEDIUM",
    )


def _check_pm9(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    risks = evidence.get("risks", [])
    if not risks:
        findings.append("Risk register evidence is empty")
    else:
        for risk in risks:
            likelihood = float(risk.get("likelihood", 0))
            impact = float(risk.get("impact", 0))
            score = float(risk.get("score", 0))
            approved = bool(risk.get("approved", False))
            mitigation = str(risk.get("mitigation", "")).strip()
            if abs((likelihood * impact) - score) > 0.01:
                findings.append(f"Risk {risk.get('id', 'unknown')} has invalid score calculation")
            if score >= 9 and not mitigation:
                findings.append(f"Risk {risk.get('id', 'unknown')} missing mitigation plan")
            if score >= 6 and not approved:
                findings.append(f"Risk {risk.get('id', 'unknown')} missing approval for moderate/high risk")

    return _result(findings, ["Validate likelihood × impact scoring", "Ensure moderate/high risks are approved and mitigated"], "MEDIUM")


def _check_ac2(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    account_events = evidence.get("account_events", [])
    tickets = evidence.get("approved_tickets", [])
    tickets_by_account = {
        str(ticket.get("account_id", "")).lower(): bool(ticket.get("isso_approved", False))
        for ticket in tickets
    }

    if not account_events:
        findings.append("No account creation events provided")
    for event in account_events:
        account_id = str(event.get("account_id", "")).lower()
        if not account_id:
            findings.append("Account event missing account_id")
            continue
        if not tickets_by_account.get(account_id, False):
            findings.append(f"Unauthorized account event detected for {account_id}")

    return _result(findings, ["Correlate all account creation events to ISSO-approved tickets"], "HIGH")


def _check_ac7(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    failed_logons = evidence.get("failed_logons", [])
    lockouts = set(str(item).lower() for item in evidence.get("lockouts", []))

    if not failed_logons:
        findings.append("No failed logon evidence provided")
    else:
        fail_counts: dict[str, int] = {}
        for event in failed_logons:
            username = str(event.get("username", "")).lower()
            if not username:
                continue
            fail_counts[username] = fail_counts.get(username, 0) + 1
        for username, count in fail_counts.items():
            if count >= 3 and username not in lockouts:
                findings.append(f"Lockout missing for user {username} after {count} failures")

    return _result(findings, ["Enforce account lockout after failed authentication threshold"], "HIGH")


def _check_au3(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    records = evidence.get("records", [])
    required = {"timestamp", "event_type", "subject", "outcome", "source_ip"}

    if not records:
        findings.append("No audit records provided")
    else:
        incomplete = 0
        for record in records:
            missing = [field for field in required if not str(record.get(field, "")).strip()]
            if missing:
                incomplete += 1
        completeness = 1 - (incomplete / max(len(records), 1))
        if completeness < 0.95:
            findings.append(f"Audit record completeness below threshold: {round(completeness * 100, 1)}%")

    return _result(findings, ["Ensure required AU-3 fields are present in all sampled records"], "MEDIUM")


def _check_cm8(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []

    collection_error = evidence.get("collection_error")
    if collection_error:
        findings.append(f"AWS SSM inventory collection failed: {collection_error}")

    expected = set(str(item).lower() for item in evidence.get("inventory_expected", []))
    discovered = set(str(item).lower() for item in evidence.get("inventory_discovered", []))

    if not expected and not discovered and not collection_error:
        findings.append("No CM-8 inventory evidence provided")
    else:
        orphans = sorted(expected - discovered)
        shadow = sorted(discovered - expected)
        if orphans:
            findings.append(f"Inventory records missing in discovered set: {len(orphans)}")
        if shadow:
            findings.append(f"Discovered unmanaged assets (shadow IT): {len(shadow)}")

    return _result(findings, ["Reconcile expected and discovered inventory sets", "Verify AWS SSM connectivity and IAM permissions"], "MEDIUM")


def _check_ia5(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    policy = evidence.get("policy", {})

    if not policy:
        findings.append("No IA-5 policy evidence provided")
    else:
        if int(policy.get("MinimumLength", 0)) < 14:
            findings.append("MinimumLength must be at least 14")
        if not bool(policy.get("ComplexityEnabled", False)):
            findings.append("ComplexityEnabled must be true")
        if int(policy.get("PasswordHistory", 0)) < 24:
            findings.append("PasswordHistory must be at least 24")
        if int(policy.get("MaximumAge", 999)) > 60:
            findings.append("MaximumAge must be 60 days or less")

    return _result(findings, ["Align policy with NIST 800-63B thresholds"], "MEDIUM")


def _check_ra5(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    vulnerabilities = evidence.get("vulnerabilities", [])
    if not vulnerabilities:
        findings.append("No vulnerability evidence provided")
    else:
        for vuln in vulnerabilities:
            cvss = float(vuln.get("cvss_score", 0))
            days_open = int(vuln.get("days_open", 0))
            if cvss >= 9.0 and days_open > 15:
                findings.append(f"Critical vulnerability exceeds SLA: {vuln.get('cve', 'unknown')}")
            elif cvss >= 7.0 and days_open > 30:
                findings.append(f"High vulnerability exceeds SLA: {vuln.get('cve', 'unknown')}")
            elif cvss >= 4.0 and days_open > 90:
                findings.append(f"Moderate vulnerability exceeds SLA: {vuln.get('cve', 'unknown')}")

    return _result(findings, ["Remediate vulnerabilities based on CVSS SLA thresholds"], "HIGH")


def _check_si2(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []

    collection_error = evidence.get("collection_error")
    if collection_error:
        findings.append(f"AWS SSM patch state collection failed: {collection_error}")

    patches = evidence.get("patches", [])

    if not patches and not collection_error:
        findings.append("No SI-2 patch evidence provided")
    elif patches:
        for patch in patches:
            severity = str(patch.get("severity", "")).upper()
            days_open = int(patch.get("days_open", 0))
            compensating = bool(patch.get("compensating_control", False))
            in_kev = bool(patch.get("in_kev", False))
            if severity == "CRITICAL" and days_open > 15 and not compensating:
                findings.append(f"Critical patch SLA exceeded without compensating control: {patch.get('cve', 'unknown')}")
            if severity == "HIGH" and days_open > 30 and not compensating:
                findings.append(f"High patch SLA exceeded without compensating control: {patch.get('cve', 'unknown')}")
            if in_kev and days_open > 7 and not compensating:
                findings.append(f"KEV-listed vulnerability overdue or missing compensating control: {patch.get('cve', 'unknown')}")

    return _result(findings, ["Patch within SLA or document compensating controls", "Cross-reference vulnerabilities with NVD and CISA KEV"], "HIGH")


def _check_si4(evidence: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []

    collection_error = evidence.get("collection_error")
    if collection_error:
        findings.append(f"AWS CloudWatch log collection failed: {collection_error}")
        return _result(
            findings,
            ["Verify CloudWatch log group name and AWS credentials/permissions"],
            "HIGH",
        )

    hourly_counts = evidence.get("hourly_event_counts", [])
    anomaly_hours = list(evidence.get("anomaly_hours", []))

    if len(hourly_counts) != 24:
        findings.append("SI-4 requires 24 hourly event buckets")
    else:
        gaps = [i for i, count in enumerate(hourly_counts) if int(count) == 0]
        if gaps:
            findings.append(f"Monitoring gaps detected in hours: {gaps}")
        if anomaly_hours:
            findings.append(f"Log volume anomalies detected in hours: {anomaly_hours}")

    return _result(findings, ["Ensure continuous monitoring with no hourly log gaps", "Investigate anomalous log volume spikes/drops"], "HIGH")
