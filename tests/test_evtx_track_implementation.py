from pathlib import Path

from src.agents.orchestrator import BOBBIEOrchestrator
from src.parsers import parse_event_xml_records


def _xml(event_id: int, target_user: str = "user1", ip: str = "10.0.0.2", include_email: bool = False) -> str:
    email_payload = "alice@example.com" if include_email else ""
    return f"""
<Event>
  <System>
    <Provider Name="Microsoft-Windows-Security-Auditing" />
    <EventID>{event_id}</EventID>
    <TimeCreated SystemTime="2026-02-14T12:00:00.000Z" />
    <Channel>Security</Channel>
    <Computer>WIN-TEST</Computer>
  </System>
  <EventData>
    <Data Name="TargetUserName">{target_user}</Data>
    <Data Name="SubjectUserName">admin</Data>
    <Data Name="IpAddress">{ip}</Data>
    <Data Name="Message">{email_payload}</Data>
  </EventData>
</Event>
""".strip()


def test_parse_required_windows_events_from_xml_records() -> None:
    xml_records = [
        _xml(4625, "user-lock"),
        _xml(4720, "svc-app-01"),
        _xml(4722, "svc-app-01"),
        _xml(4738, "svc-app-01"),
        _xml(4740, "user-lock"),
    ]

    events = parse_event_xml_records(xml_records)
    event_ids = {item["event_id"] for item in events}

    assert event_ids == {4625, 4720, 4722, 4738, 4740}


def test_ac2_ac7_from_evtx_context_performs_correlation_and_lockout_checks() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    xml_records = [
        _xml(4720, "svc-app-01"),
        _xml(4722, "svc-app-01"),
        _xml(4625, "locked-user"),
        _xml(4625, "locked-user"),
        _xml(4625, "locked-user"),
        _xml(4740, "locked-user"),
    ]

    context = {
        "repo_root": str(root),
        "evtx": {
            "xml_records": xml_records,
            "approved_tickets": [{"account_id": "svc-app-01", "isso_approved": True}],
        },
    }

    result = orchestrator.run({"AC": ["AC-2", "AC-7"]}, context=context)
    ac2 = result["families"]["AC"]["controls"]["AC-2"]
    ac7 = result["families"]["AC"]["controls"]["AC-7"]

    assert ac2["status"] == "PASS"
    assert ac7["status"] == "PASS"


def test_au3_from_evtx_context_runs_field_completeness_and_sensitive_pattern_checks() -> None:
    root = Path(__file__).resolve().parent.parent
    orchestrator = BOBBIEOrchestrator()

    xml_records = [
        _xml(4625, "user-pii", include_email=True),
        _xml(4720, "svc-app-02"),
    ]

    context = {
        "repo_root": str(root),
        "evtx": {
            "xml_records": xml_records,
        },
    }

    result = orchestrator.run({"AU": ["AU-3"]}, context=context)
    au3 = result["families"]["AU"]["controls"]["AU-3"]

    assert au3["status"] == "FAIL"
    assert au3["evidence"]["effectiveness"] == "INEFFECTIVE"
    assert any("PII" in finding or "sensitive" in finding.lower() for finding in au3["findings"])
