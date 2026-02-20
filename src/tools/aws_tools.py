from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any

import requests


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_hour(ts_ms: int) -> datetime:
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0)


def detect_hourly_gaps_anomalies(hourly_event_counts: list[int], z_threshold: float = 2.5) -> dict[str, Any]:
    if len(hourly_event_counts) != 24:
        return {
            "gap_hours": [],
            "anomaly_hours": [],
            "mean": 0.0,
            "stddev": 0.0,
            "valid": False,
        }

    gaps = [idx for idx, count in enumerate(hourly_event_counts) if int(count) == 0]
    avg = mean(hourly_event_counts)
    std = pstdev(hourly_event_counts)

    anomalies: list[int] = []
    if std > 0:
        for idx, count in enumerate(hourly_event_counts):
            z = abs((count - avg) / std)
            if z >= z_threshold:
                anomalies.append(idx)

    return {
        "gap_hours": gaps,
        "anomaly_hours": anomalies,
        "mean": float(round(avg, 4)),
        "stddev": float(round(std, 4)),
        "valid": True,
    }


@dataclass
class CloudWatchEvidenceCollector:
    logs_client: Any | None = None

    def collect(self, log_group: str, hours: int = 24, now: datetime | None = None) -> dict[str, Any]:
        if self.logs_client is None:
            return {
                "hourly_event_counts": [],
                "total_events": 0,
                "gap_hours": [],
                "anomaly_hours": [],
                "error": "CloudWatch logs client is not configured",
            }

        end_time = now or _utc_now()
        start_time = end_time - timedelta(hours=hours)
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)

        events: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "logGroupName": log_group,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": 10000,
            }
            if next_token:
                params["nextToken"] = next_token

            response = self.logs_client.filter_log_events(**params)
            batch = response.get("events", [])
            events.extend(batch)

            new_token = response.get("nextToken")
            if not new_token or new_token == next_token:
                break
            next_token = new_token

        hour_buckets: dict[datetime, int] = {}
        for event in events:
            ts_ms = int(event.get("timestamp", 0))
            bucket = _normalize_hour(ts_ms)
            hour_buckets[bucket] = hour_buckets.get(bucket, 0) + 1

        ordered_hours: list[datetime] = []
        cursor = start_time.replace(minute=0, second=0, microsecond=0)
        for _ in range(hours):
            ordered_hours.append(cursor)
            cursor += timedelta(hours=1)

        hourly_counts = [hour_buckets.get(hour, 0) for hour in ordered_hours[-24:]]
        stats = detect_hourly_gaps_anomalies(hourly_counts)

        return {
            "hourly_event_counts": hourly_counts,
            "total_events": len(events),
            "gap_hours": stats["gap_hours"],
            "anomaly_hours": stats["anomaly_hours"],
        }


@dataclass
class SSMInventoryCollector:
    ssm_client: Any | None = None

    def collect_instance_ids(self) -> list[str]:
        if self.ssm_client is None:
            return []

        response = self.ssm_client.describe_instance_information()
        instances = response.get("InstanceInformationList", [])
        return [str(item.get("InstanceId", "")).strip() for item in instances if str(item.get("InstanceId", "")).strip()]


def reconcile_inventory(expected: list[str], discovered: list[str]) -> dict[str, Any]:
    expected_set = {item.lower() for item in expected if item}
    discovered_set = {item.lower() for item in discovered if item}
    missing = sorted(expected_set - discovered_set)
    unmanaged = sorted(discovered_set - expected_set)
    return {
        "inventory_expected": sorted(expected_set),
        "inventory_discovered": sorted(discovered_set),
        "missing_count": len(missing),
        "unmanaged_count": len(unmanaged),
        "missing_assets": missing,
        "unmanaged_assets": unmanaged,
    }


@dataclass
class SSMPatchCollector:
    ssm_client: Any | None = None

    def collect_patch_states(self, instance_ids: list[str]) -> list[dict[str, Any]]:
        if self.ssm_client is None or not instance_ids:
            return []

        response = self.ssm_client.describe_instance_patch_states(InstanceIds=instance_ids)
        states = response.get("InstancePatchStates", [])
        patches: list[dict[str, Any]] = []
        for state in states:
            patches.append(
                {
                    "instance_id": state.get("InstanceId"),
                    "missing_count": int(state.get("MissingCount", 0) or 0),
                    "critical_non_compliant_count": int(state.get("CriticalNonCompliantCount", 0) or 0),
                    "security_non_compliant_count": int(state.get("SecurityNonCompliantCount", 0) or 0),
                }
            )
        return patches


@dataclass
class NVDKEVEnricher:
    session: requests.Session | None = None

    def enrich(self, patches: list[dict[str, Any]], kev_vulns: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        kev_vulns = kev_vulns or []
        kev_ids = {
            str(item.get("cveID", "")).upper()
            for item in kev_vulns
            if isinstance(item, dict) and str(item.get("cveID", "")).strip()
        }

        enriched: list[dict[str, Any]] = []
        for patch in patches:
            cve = str(patch.get("cve", "")).upper().strip()
            item = dict(patch)
            item["in_kev"] = cve in kev_ids if cve else False
            enriched.append(item)
        return enriched
