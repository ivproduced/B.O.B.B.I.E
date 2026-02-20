from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


REQUIRED_EVENT_IDS = {4625, 4720, 4722, 4738, 4740}


def _tag(name: str) -> str:
    return f"{{*}}{name}"


def _event_data_map(root: ET.Element) -> dict[str, str]:
    data: dict[str, str] = {}
    for node in root.findall(f".//{_tag('EventData')}/{_tag('Data')}"):
        key = str(node.attrib.get("Name", "")).strip()
        if not key:
            continue
        data[key] = (node.text or "").strip()
    return data


def _parse_event_xml(xml_text: str) -> dict[str, Any] | None:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    event_id_text = root.findtext(f".//{_tag('System')}/{_tag('EventID')}", default="").strip()
    if not event_id_text:
        return None

    try:
        event_id = int(event_id_text)
    except ValueError:
        return None

    timestamp = ""
    time_node = root.find(f".//{_tag('System')}/{_tag('TimeCreated')}")
    if time_node is not None:
        timestamp = str(time_node.attrib.get("SystemTime", "")).strip()

    data = _event_data_map(root)
    channel = root.findtext(f".//{_tag('System')}/{_tag('Channel')}", default="").strip()
    computer = root.findtext(f".//{_tag('System')}/{_tag('Computer')}", default="").strip()

    return {
        "event_id": event_id,
        "timestamp": timestamp,
        "channel": channel,
        "computer": computer,
        "data": data,
    }


def parse_event_xml_records(xml_records: list[str], event_ids: set[int] | None = None) -> list[dict[str, Any]]:
    allowed = event_ids or REQUIRED_EVENT_IDS
    parsed: list[dict[str, Any]] = []
    for xml_text in xml_records:
        event = _parse_event_xml(xml_text)
        if event is None:
            continue
        if event["event_id"] in allowed:
            parsed.append(event)
    return parsed


def parse_security_log(evtx_path: str, event_ids: set[int] | None = None) -> list[dict[str, Any]]:
    path = Path(evtx_path)
    if not path.exists() or not path.is_file():
        return []

    try:
        import Evtx.Evtx as evtx
    except Exception:
        return []

    allowed = event_ids or REQUIRED_EVENT_IDS
    events: list[dict[str, Any]] = []
    with evtx.Evtx(str(path)) as log:
        for record in log.records():
            event = _parse_event_xml(record.xml())
            if event is None:
                continue
            if event["event_id"] in allowed:
                events.append(event)
    return events


def _to_audit_record(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data", {})
    event_id = int(event.get("event_id", 0))
    subject = str(data.get("TargetUserName") or data.get("SubjectUserName") or "").strip()
    source_ip = str(data.get("IpAddress") or data.get("WorkstationName") or "").strip()
    outcome = "FAILURE" if event_id == 4625 else "SUCCESS"

    return {
        "timestamp": str(event.get("timestamp", "")).strip(),
        "event_type": str(event_id),
        "subject": subject,
        "outcome": outcome,
        "source_ip": source_ip,
    }


def _contains_sensitive_pattern(text: str) -> bool:
    patterns = [
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"\b(?:\d[ -]*?){13,16}\b",
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def build_evtx_control_evidence(events: list[dict[str, Any]], approved_tickets: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    approved_tickets = approved_tickets or []

    ac2_events = [
        {
            "account_id": str(event.get("data", {}).get("TargetUserName", "")).strip().lower(),
            "event_id": event.get("event_id"),
            "timestamp": event.get("timestamp"),
        }
        for event in events
        if int(event.get("event_id", 0)) in {4720, 4722, 4738}
        and str(event.get("data", {}).get("TargetUserName", "")).strip()
    ]

    failed_logons = [
        {
            "username": str(event.get("data", {}).get("TargetUserName", "")).strip().lower(),
            "timestamp": event.get("timestamp"),
        }
        for event in events
        if int(event.get("event_id", 0)) == 4625
        and str(event.get("data", {}).get("TargetUserName", "")).strip()
    ]

    lockouts = [
        str(event.get("data", {}).get("TargetUserName", "")).strip().lower()
        for event in events
        if int(event.get("event_id", 0)) == 4740
        and str(event.get("data", {}).get("TargetUserName", "")).strip()
    ]

    records = [_to_audit_record(event) for event in events]

    pii_detections = 0
    for event in events:
        payload = " ".join(str(value) for value in event.get("data", {}).values())
        if _contains_sensitive_pattern(payload):
            pii_detections += 1

    return {
        "AC-2": {
            "account_events": ac2_events,
            "approved_tickets": approved_tickets,
            "status_change_notifications": bool(ac2_events),
        },
        "AC-7": {
            "failed_logons": failed_logons,
            "lockouts": lockouts,
        },
        "AU-3": {
            "records": records,
            "pii_detections": pii_detections,
        },
    }


@dataclass
class EVTXEvidenceCollector:
    def collect_from_context(self, context: dict[str, Any]) -> dict[str, dict[str, Any]]:
        evtx = context.get("evtx", {}) if isinstance(context.get("evtx", {}), dict) else {}
        xml_records = list(evtx.get("xml_records", []))
        approved_tickets = list(evtx.get("approved_tickets", context.get("approved_tickets", [])))

        if xml_records:
            events = parse_event_xml_records(xml_records, event_ids=REQUIRED_EVENT_IDS)
            return build_evtx_control_evidence(events, approved_tickets=approved_tickets)

        log_path = str(evtx.get("security_log_path", "")).strip()
        if log_path:
            events = parse_security_log(log_path, event_ids=REQUIRED_EVENT_IDS)
            return build_evtx_control_evidence(events, approved_tickets=approved_tickets)

        return {}
