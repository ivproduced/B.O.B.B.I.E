"""
generate_test_data.py
=====================
Generates deterministic test scenario JSON files into data/test_scenarios/.

Scenarios produced:
  scenario_pass.json        – all 10 controls have clean/passing evidence
  scenario_fail.json        – every control has at least one failing condition
  scenario_mixed.json       – realistic partial compliance (some pass, some fail)
  scenario_evtx_clean.json  – clean Windows Security event stream only
  scenario_evtx_brute_force.json – brute-force + lockout event stream

Evidence shapes are derived directly from the NIST SP 800-53 Rev 5 catalog
and the B.O.B.B.I.E evidence_checks.py evaluators for:
  PL-2, PM-9, AC-2, AC-7, AU-3, CM-8, IA-5, RA-5, SI-2, SI-4
"""
from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "data" / "test_scenarios"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# EVTX XML record helpers
# ---------------------------------------------------------------------------

def _evtx_record(event_id: int, time: str, computer: str, user: str, actor: str, ip: str, msg: str) -> str:
    return (
        f'<Event><System>'
        f'<Provider Name="Microsoft-Windows-Security-Auditing"/>'
        f'<EventID>{event_id}</EventID>'
        f'<TimeCreated SystemTime="{time}"/>'
        f'<Channel>Security</Channel>'
        f'<Computer>{computer}</Computer>'
        f'</System><EventData>'
        f'<Data Name="TargetUserName">{user}</Data>'
        f'<Data Name="SubjectUserName">{actor}</Data>'
        f'<Data Name="IpAddress">{ip}</Data>'
        f'<Data Name="Message">{msg}</Data>'
        f'</EventData></Event>'
    )


EVTX_CLEAN = [
    # 4720 – account created (approved service account)
    _evtx_record(4720, "2026-02-14T08:00:00.000Z", "WIN-DC01", "svc-app-01", "admin", "10.0.0.10", "Account created"),
    # 4738 – account changed
    _evtx_record(4738, "2026-02-14T08:05:00.000Z", "WIN-DC01", "svc-app-01", "admin", "10.0.0.10", "Account changed"),
    # 4634 – logoff
    _evtx_record(4634, "2026-02-14T17:00:00.000Z", "WIN-DC01", "svc-app-01", "SYSTEM", "10.0.0.10", "Account logoff"),
    # 4648 – explicit credential logon
    _evtx_record(4648, "2026-02-14T09:00:00.000Z", "WIN-DC01", "alice", "alice", "10.0.0.20", "Explicit credentials used"),
    # 4624 – successful logon
    _evtx_record(4624, "2026-02-14T09:01:00.000Z", "WIN-DC01", "alice", "SYSTEM", "10.0.0.20", "Logon success"),
]

EVTX_BRUTE_FORCE = [
    # account creation
    _evtx_record(4720, "2026-02-14T12:00:00.000Z", "WIN-DEMO", "svc-app-01", "admin", "10.0.0.10", "Account created"),
    # 5 rapid failed logons → triggers lockout
    *[
        _evtx_record(4625, f"2026-02-14T12:0{5+i}:00.000Z", "WIN-DEMO", "alice", "SYSTEM", "192.168.99.99", "Failed logon attempt")
        for i in range(5)
    ],
    # 4740 – account locked out
    _evtx_record(4740, "2026-02-14T12:10:00.000Z", "WIN-DEMO", "alice", "SYSTEM", "192.168.99.99", "Account lockout"),
    # privilege escalation attempt
    _evtx_record(4672, "2026-02-14T12:15:00.000Z", "WIN-DEMO", "attacker", "SYSTEM", "192.168.99.99", "Special privileges assigned to new logon"),
    # 4738 – account modified post-lockout (suspicious)
    _evtx_record(4738, "2026-02-14T12:16:00.000Z", "WIN-DEMO", "alice", "attacker", "192.168.99.99", "Account changed after lockout"),
]

APPROVED_TICKETS_CLEAN = [
    {"account_id": "svc-app-01", "isso_approved": True},
    {"account_id": "alice", "isso_approved": True},
]

APPROVED_TICKETS_FAIL = [
    {"account_id": "svc-app-01", "isso_approved": False},
]

AU3_RECORDS_COMPLETE = [
    {"timestamp": "2026-02-14T08:00:00.000Z", "event_type": "4720", "subject": "svc-app-01", "outcome": "SUCCESS", "source_ip": "10.0.0.10"},
    {"timestamp": "2026-02-14T08:05:00.000Z", "event_type": "4738", "subject": "svc-app-01", "outcome": "SUCCESS", "source_ip": "10.0.0.10"},
    {"timestamp": "2026-02-14T09:00:00.000Z", "event_type": "4624", "subject": "alice",      "outcome": "SUCCESS", "source_ip": "10.0.0.20"},
    {"timestamp": "2026-02-14T17:00:00.000Z", "event_type": "4634", "subject": "alice",      "outcome": "SUCCESS", "source_ip": "10.0.0.20"},
]

AU3_RECORDS_INCOMPLETE = [
    # Missing required fields (no outcome, no source_ip)
    {"timestamp": "2026-02-14T09:00:00.000Z", "event_type": "4624"},
    {"timestamp": "2026-02-14T10:00:00.000Z"},
]

# ---------------------------------------------------------------------------
# Per-control evidence builders
# ---------------------------------------------------------------------------

def pl2_pass() -> dict:
    return {
        "sections_present": ["system-characteristics", "control-implementation", "system-implementation", "metadata"],
        "missing_baseline_controls": 0,
        "stale_approvals": 0,
    }

def pl2_fail() -> dict:
    return {
        "sections_present": ["metadata"],   # missing required sections
        "missing_baseline_controls": 5,
        "stale_approvals": 3,
    }

def pm9_pass() -> dict:
    return {
        "risks": [
            {"id": "R-001", "likelihood": 2, "impact": 3, "score": 6,  "approved": True,  "mitigation": "Segmentation and monitoring controls"},
            {"id": "R-002", "likelihood": 1, "impact": 2, "score": 2,  "approved": True,  "mitigation": "Compensating detective control"},
            {"id": "R-003", "likelihood": 1, "impact": 1, "score": 1,  "approved": True,  "mitigation": "Risk accepted; documented in risk register"},
        ]
    }

def pm9_fail() -> dict:
    return {
        "risks": [
            # score > 15 (likelihood × impact) and not approved → triggers failure
            {"id": "R-001", "likelihood": 5, "impact": 5, "score": 25, "approved": False, "mitigation": ""},
            {"id": "R-002", "likelihood": 4, "impact": 4, "score": 16, "approved": False, "mitigation": ""},
        ]
    }

def ac2_pass() -> dict:
    """AC-2 evidence uses EVTX xml_records + approved_tickets at top-level context."""
    return {}   # AC-2 reads from evtx.xml_records and evtx.approved_tickets

def ac7_pass() -> dict:
    return {
        "lockout_threshold": 5,
        "lockout_events": [],
        "failed_logons_24h": 0,
    }

def ac7_fail() -> dict:
    return {
        "lockout_threshold": 5,
        "lockout_events": [
            {"account": "alice", "time": "2026-02-14T12:10:00Z", "ip": "192.168.99.99"},
        ],
        "failed_logons_24h": 87,
    }

def au3_pass() -> dict:
    return {"records": AU3_RECORDS_COMPLETE}

def au3_fail() -> dict:
    return {"records": AU3_RECORDS_INCOMPLETE}

def cm8_pass() -> dict:
    return {
        "inventory_expected":   ["i-001", "i-002", "i-003", "i-004"],
        "inventory_discovered": ["i-001", "i-002", "i-003", "i-004"],
    }

def cm8_fail() -> dict:
    return {
        "inventory_expected":   ["i-001", "i-002", "i-003", "i-004"],
        "inventory_discovered": ["i-001", "i-002"],          # i-003, i-004 missing → unmanaged gap
        "ssm_inventory":        ["i-001", "i-002", "i-099"], # i-099 undiscovered/rogue
    }

def ia5_pass() -> dict:
    return {
        "policy": {
            "MinimumLength":    14,
            "ComplexityEnabled": True,
            "PasswordHistory":  24,
            "MaximumAge":       60,
        },
        "weak_algorithms": [],
    }

def ia5_fail() -> dict:
    return {
        "policy": {
            "MinimumLength":    6,   # too short (NIST 800-53 requires ≥ 8, sp 800-63 ≥ 15)
            "ComplexityEnabled": False,
            "PasswordHistory":  3,   # too low
            "MaximumAge":       365, # too long (> 90 days)
        },
        "weak_algorithms": ["MD5", "DES"],
    }

def ra5_pass() -> dict:
    return {
        "vulnerabilities": [
            {"cve": "CVE-2025-0101", "cvss_score": 4.0, "days_open": 14, "in_kev": False},
            {"cve": "CVE-2025-0202", "cvss_score": 6.5, "days_open": 20, "in_kev": False},
        ],
        "scan_coverage":  1.0,
        "scan_age_hours": 12,
    }

def ra5_fail() -> dict:
    return {
        "vulnerabilities": [
            # CRITICAL in KEV and over SLA → failure
            {"cve": "CVE-2025-9999", "cvss_score": 9.8, "days_open": 45, "in_kev": True},
            # HIGH open > 30 days → SLA breach
            {"cve": "CVE-2025-8888", "cvss_score": 7.5, "days_open": 62, "in_kev": False},
        ],
        "scan_coverage":  0.4,   # < full coverage
        "scan_age_hours": 200,   # stale scan (> 168 h / 1 week)
    }

def si2_pass() -> dict:
    return {
        "patches": [
            {"cve": "CVE-2025-1111", "severity": "CRITICAL", "days_open": 7,  "compensating_control": True,  "in_kev": False},
            {"cve": "CVE-2025-2222", "severity": "HIGH",     "days_open": 10, "compensating_control": True,  "in_kev": False},
            {"cve": "CVE-2025-3333", "severity": "MEDIUM",   "days_open": 25, "compensating_control": False, "in_kev": False},
        ]
    }

def si2_fail() -> dict:
    return {
        "patches": [
            # CRITICAL in KEV with no compensating control → failure
            {"cve": "CVE-2025-7777", "severity": "CRITICAL", "days_open": 30, "compensating_control": False, "in_kev": True},
            # HIGH overdue
            {"cve": "CVE-2025-6666", "severity": "HIGH",     "days_open": 60, "compensating_control": False, "in_kev": False},
        ]
    }

def si4_pass() -> dict:
    return {
        # 24 hours of stable hourly counts – no anomaly hours
        "hourly_event_counts": [12, 13, 11, 14, 10, 12, 13, 11, 14, 12, 10, 11, 13, 12, 10, 11, 12, 14, 13, 12, 11, 10, 12, 13],
        "anomaly_hours": [],
    }

def si4_fail() -> dict:
    counts = [12, 13, 11, 14, 10, 12, 13, 11, 14, 12, 10, 11, 13, 12, 10, 11, 12, 14, 13, 12, 11, 10, 12, 13]
    counts[3]  = 980   # spike at hour 03
    counts[15] = 0     # gap at hour 15
    return {
        "hourly_event_counts": counts,
        "anomaly_hours": [3, 15],
    }

# ---------------------------------------------------------------------------
# Full context assemblers
# ---------------------------------------------------------------------------

def _context(ce: dict, evtx_records: list, approved_tickets: list) -> dict:
    return {
        "control_evidence": ce,
        "evtx": {
            "xml_records":      evtx_records,
            "approved_tickets": approved_tickets,
        },
    }


SCENARIO_PASS = _context(
    ce={
        "PL-2": pl2_pass(),
        "PM-9": pm9_pass(),
        "AC-7": ac7_pass(),
        "AU-3": au3_pass(),
        "CM-8": cm8_pass(),
        "IA-5": ia5_pass(),
        "RA-5": ra5_pass(),
        "SI-2": si2_pass(),
        "SI-4": si4_pass(),
    },
    evtx_records=EVTX_CLEAN,
    approved_tickets=APPROVED_TICKETS_CLEAN,
)

SCENARIO_FAIL = _context(
    ce={
        "PL-2": pl2_fail(),
        "PM-9": pm9_fail(),
        "AC-7": ac7_fail(),
        "AU-3": au3_fail(),
        "CM-8": cm8_fail(),
        "IA-5": ia5_fail(),
        "RA-5": ra5_fail(),
        "SI-2": si2_fail(),
        "SI-4": si4_fail(),
    },
    evtx_records=EVTX_BRUTE_FORCE,
    approved_tickets=APPROVED_TICKETS_FAIL,
)

SCENARIO_MIXED = _context(
    ce={
        # Passing controls
        "PL-2": pl2_pass(),
        "IA-5": ia5_pass(),
        "CM-8": cm8_pass(),
        "SI-4": si4_pass(),
        # Failing controls
        "PM-9": pm9_fail(),
        "AU-3": au3_fail(),
        "RA-5": ra5_fail(),
        "SI-2": si2_fail(),
        "AC-7": ac7_fail(),
    },
    evtx_records=EVTX_CLEAN,
    approved_tickets=APPROVED_TICKETS_CLEAN,
)

SCENARIO_EVTX_CLEAN = _context(
    ce={},
    evtx_records=EVTX_CLEAN,
    approved_tickets=APPROVED_TICKETS_CLEAN,
)

SCENARIO_EVTX_BRUTE_FORCE = _context(
    ce={},
    evtx_records=EVTX_BRUTE_FORCE,
    approved_tickets=APPROVED_TICKETS_FAIL,
)

# ---------------------------------------------------------------------------
# Write files
# ---------------------------------------------------------------------------

SCENARIOS: dict[str, dict] = {
    "scenario_pass.json":             SCENARIO_PASS,
    "scenario_fail.json":             SCENARIO_FAIL,
    "scenario_mixed.json":            SCENARIO_MIXED,
    "scenario_evtx_clean.json":       SCENARIO_EVTX_CLEAN,
    "scenario_evtx_brute_force.json": SCENARIO_EVTX_BRUTE_FORCE,
}

if __name__ == "__main__":
    for filename, data in SCENARIOS.items():
        path = OUT_DIR / filename
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"  wrote {path.relative_to(Path(__file__).parent.parent)}")
    print(f"\nDone — {len(SCENARIOS)} scenario files in data/test_scenarios/")
