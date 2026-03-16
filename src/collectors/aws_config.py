"""
AWS Config snapshot collector.

Two modes:
  1. File mode  – pass a path to a locally-downloaded Config snapshot JSON.
  2. Live mode  – trigger AWS Config to deliver a fresh snapshot to S3 and
                  download it immediately.  Requires:
                    - s3_bucket: the S3 bucket configured as Config delivery channel
                    - s3_prefix: (optional) key prefix  e.g. "AWSLogs/123456789012/Config/us-east-1"

AWS Config snapshots use CloudFormation resource type strings natively, so no
mapping is required — we just group the resource items by resourceType.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from src.collectors.base import InfraSnapshot, _utc_now


def _boto_session(profile: str | None, region: str):
    import boto3
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)
    return boto3.Session(region_name=region)


def _trigger_and_download(
    s3_bucket: str,
    s3_prefix: str | None,
    aws_profile: str | None,
    aws_region: str,
) -> tuple[dict[str, Any], list[str]]:
    """Deliver a fresh Config snapshot to S3 and return the parsed JSON."""
    errors: list[str] = []
    session = _boto_session(aws_profile, aws_region)
    config_client = session.client("config")
    s3_client = session.client("s3")

    # Identify the delivery channel name
    channel_name = "default"
    try:
        channels = config_client.describe_delivery_channels()
        if channels["DeliveryChannels"]:
            ch = channels["DeliveryChannels"][0]
            channel_name = ch["name"]
            if not s3_bucket:
                s3_bucket = ch.get("s3BucketName", s3_bucket)
    except Exception as exc:
        errors.append(f"Could not list Config delivery channels: {exc}")

    # Trigger snapshot delivery
    try:
        config_client.deliver_config_snapshot(deliveryChannelName=channel_name)
    except Exception as exc:
        errors.append(f"Failed to trigger Config snapshot delivery: {exc}")

    if not s3_bucket:
        errors.append("No S3 bucket specified or discoverable for AWS Config snapshot download.")
        return {}, errors

    # Wait briefly for snapshot to land in S3 (Config usually delivers within ~5-15s)
    snapshot_key: str | None = None
    deadline = time.time() + 120  # 2-minute timeout
    prefix = s3_prefix or ""
    while time.time() < deadline:
        try:
            resp = s3_client.list_objects_v2(
                Bucket=s3_bucket,
                Prefix=prefix,
            )
            # Find the most-recently-modified ConfigSnapshot object
            objs = [
                o for o in resp.get("Contents", [])
                if "ConfigSnapshot" in o["Key"] and o["Key"].endswith(".json.gz") or
                   "ConfigSnapshot" in o["Key"] and o["Key"].endswith(".json")
            ]
            if objs:
                objs.sort(key=lambda o: o["LastModified"], reverse=True)
                snapshot_key = objs[0]["Key"]
                break
        except Exception as exc:
            errors.append(f"S3 list error: {exc}")
            break
        time.sleep(5)

    if not snapshot_key:
        errors.append("Timed out waiting for Config snapshot in S3.")
        return {}, errors

    try:
        obj = s3_client.get_object(Bucket=s3_bucket, Key=snapshot_key)
        body = obj["Body"].read()
        # Handle gzip
        if snapshot_key.endswith(".gz"):
            import gzip
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8")), errors
    except Exception as exc:
        errors.append(f"Failed to download/parse Config snapshot: {exc}")
        return {}, errors


def _parse_snapshot(raw: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], str]:
    """Group Config configurationItems by resourceType."""
    resources: dict[str, list[dict[str, Any]]] = {}
    account_id = "unknown"

    items = raw.get("configurationItems", [])
    for item in items:
        rtype: str = item.get("resourceType", "Unknown")
        rid: str = item.get("resourceId", "")
        rname: str = item.get("resourceName", rid)
        arn: str = item.get("ARN", "")
        config_blob = item.get("configuration", {})

        if isinstance(config_blob, str):
            try:
                config_blob = json.loads(config_blob)
            except Exception:
                config_blob = {"raw": config_blob}

        if account_id == "unknown":
            a = item.get("awsAccountId", "")
            if a:
                account_id = a

        normalized: dict[str, Any] = {
            "id":                    rid,
            "arn":                   arn,
            "name":                  rname,
            "availability_zone":     item.get("availabilityZone", ""),
            "configuration_item_status": item.get("configurationItemStatus", ""),
            "attributes":            config_blob,
            "tags":                  item.get("tags", {}),
        }
        resources.setdefault(rtype, []).append(normalized)

    return resources, account_id


def collect(
    infra_file: str | Path | None,
    s3_bucket: str | None,
    s3_prefix: str | None,
    aws_profile: str | None,
    aws_region: str,
) -> InfraSnapshot:
    errors: list[str] = []
    raw: dict[str, Any] = {}

    # ── Mode 1: local file ───────────────────────────────────────────────────
    if infra_file:
        fp = Path(infra_file)
        if not fp.exists():
            return InfraSnapshot(
                source="aws-config",
                collected_at=_utc_now(),
                account_id="unknown",
                region=aws_region,
                errors=[f"AWS Config snapshot file not found: {fp}"],
            )
        try:
            content = fp.read_bytes()
            if fp.suffix == ".gz":
                import gzip
                content = gzip.decompress(content)
            raw = json.loads(content.decode("utf-8"))
        except Exception as exc:
            return InfraSnapshot(
                source="aws-config",
                collected_at=_utc_now(),
                account_id="unknown",
                region=aws_region,
                errors=[f"Failed to parse AWS Config snapshot: {exc}"],
            )

    # ── Mode 2: trigger delivery and download from S3 ────────────────────────
    else:
        raw, download_errors = _trigger_and_download(
            s3_bucket=s3_bucket or "",
            s3_prefix=s3_prefix,
            aws_profile=aws_profile,
            aws_region=aws_region,
        )
        errors.extend(download_errors)
        if not raw:
            return InfraSnapshot(
                source="aws-config",
                collected_at=_utc_now(),
                account_id="unknown",
                region=aws_region,
                resources={},
                errors=errors,
            )

    resources, account_id = _parse_snapshot(raw)

    return InfraSnapshot(
        source="aws-config",
        collected_at=_utc_now(),
        account_id=account_id,
        region=aws_region,
        resources=resources,
        raw=raw,
        errors=errors,
    )
