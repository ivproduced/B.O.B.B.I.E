"""
Base types and dispatch for BOBBIE infrastructure collection.

Normalized snapshot format
--------------------------
{
  "source":       "terraform" | "aws-config" | "cloudformation" | "live",
  "collected_at": "<ISO-8601 UTC>",
  "account_id":   "<AWS account id or 'unknown'>",
  "region":       "<AWS region>",
  "resources": {
    "AWS::IAM::Role":         [{"id": ..., "arn": ..., "attributes": {...}}, ...],
    "AWS::S3::Bucket":        [...],
    "AWS::CloudTrail::Trail": [...],
    ...
  }
}

Resource type keys use CloudFormation notation as the universal standard so that
family agents can look up resources without caring which source produced them.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

InfraSourceType = Literal["terraform", "aws-config", "cloudformation", "live"]


@dataclass
class InfraSnapshot:
    source: str
    collected_at: str
    account_id: str
    region: str
    resources: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    # ── helpers ──────────────────────────────────────────────────────────────

    def get(self, resource_type: str) -> list[dict[str, Any]]:
        """Return all resources of a given CloudFormation-notation type."""
        return self.resources.get(resource_type, [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "collected_at": self.collected_at,
            "account_id": self.account_id,
            "region": self.region,
            "resource_counts": {k: len(v) for k, v in self.resources.items()},
            "total_resources": sum(len(v) for v in self.resources.values()),
            "errors": self.errors,
        }

    def save(self, path: str | Path) -> None:
        out = self.to_dict()
        out["resources"] = self.resources
        Path(path).write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_infrastructure(
    source: InfraSourceType = "live",
    *,
    # terraform / cloudformation / aws-config file-based options
    infra_file: str | Path | None = None,
    # aws-config specific
    config_s3_bucket: str | None = None,
    config_s3_prefix: str | None = None,
    # cloudformation specific
    stack_names: list[str] | None = None,
    # live / aws-config boto3 options
    aws_profile: str | None = None,
    aws_region: str | None = None,
) -> InfraSnapshot:
    """
    Dispatch to the appropriate collector and return a normalized InfraSnapshot.

    Parameters
    ----------
    source:             One of 'terraform', 'aws-config', 'cloudformation', 'live'.
    infra_file:         Path to a local .tfstate file (terraform) or a pre-downloaded
                        AWS Config snapshot JSON (aws-config).
    config_s3_bucket:   S3 bucket where AWS Config delivers snapshots.
    config_s3_prefix:   S3 key prefix for the Config snapshot (optional).
    stack_names:        CloudFormation stack names/ARNs to include (None = all stacks).
    aws_profile:        AWS named profile to use for boto3 sessions.
    aws_region:         AWS region (us-east-1 etc.).
    """
    if source == "terraform":
        from src.collectors.terraform import collect as _collect
        return _collect(infra_file=infra_file, region=aws_region or "us-east-1")

    if source == "aws-config":
        from src.collectors.aws_config import collect as _collect
        return _collect(
            infra_file=infra_file,
            s3_bucket=config_s3_bucket,
            s3_prefix=config_s3_prefix,
            aws_profile=aws_profile,
            aws_region=aws_region or "us-east-1",
        )

    if source == "cloudformation":
        from src.collectors.cloudformation import collect as _collect
        return _collect(
            stack_names=stack_names,
            aws_profile=aws_profile,
            aws_region=aws_region or "us-east-1",
        )

    # default: live
    from src.collectors.live import collect as _collect
    return _collect(
        aws_profile=aws_profile,
        aws_region=aws_region or "us-east-1",
    )
