"""
AWS CloudFormation / CDK collector.

Walks every stack (or a filtered list) and calls describe_stack_resources to
enumerate all deployed resources.  Resource types are already in CloudFormation
notation, so no mapping is needed.

For CDK projects, run `cdk synth` first then point at the synthesized stack
through CloudFormation — this collector reads *deployed* stacks, not local synth output.
"""
from __future__ import annotations

from typing import Any

from src.collectors.base import InfraSnapshot, _utc_now


def _boto_session(profile: str | None, region: str):
    import boto3
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)
    return boto3.Session(region_name=region)


def _list_all_stacks(cfn_client) -> list[dict[str, Any]]:
    """Return all active (non-deleted) stacks."""
    active_statuses = [
        "CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE",
        "ROLLBACK_COMPLETE", "IMPORT_COMPLETE", "IMPORT_ROLLBACK_COMPLETE",
    ]
    stacks: list[dict[str, Any]] = []
    paginator = cfn_client.get_paginator("list_stacks")
    for page in paginator.paginate(StackStatusFilter=active_statuses):
        stacks.extend(page.get("StackSummaries", []))
    return stacks


def _describe_stack_resources(cfn_client, stack_name: str) -> list[dict[str, Any]]:
    """Return all resources in a single stack."""
    items: list[dict[str, Any]] = []
    try:
        paginator = cfn_client.get_paginator("list_stack_resources")
        for page in paginator.paginate(StackName=stack_name):
            items.extend(page.get("StackResourceSummaries", []))
    except Exception as exc:
        items.append({
            "_error": str(exc),
            "StackName": stack_name,
        })
    return items


def collect(
    stack_names: list[str] | None,
    aws_profile: str | None,
    aws_region: str,
) -> InfraSnapshot:
    errors: list[str] = []
    resources: dict[str, list[dict[str, Any]]] = {}
    account_id = "unknown"

    try:
        session = _boto_session(aws_profile, aws_region)
        cfn_client = session.client("cloudformation")

        # Resolve account id
        try:
            sts = session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
        except Exception as exc:
            errors.append(f"Could not resolve AWS account id: {exc}")

        # Get target stack list
        if stack_names:
            target_stacks = [{"StackName": n} for n in stack_names]
        else:
            target_stacks = _list_all_stacks(cfn_client)

        for stack in target_stacks:
            sname = stack.get("StackName", "")
            if not sname:
                continue

            stack_resources = _describe_stack_resources(cfn_client, sname)
            for res in stack_resources:
                if "_error" in res:
                    errors.append(f"Stack {sname}: {res['_error']}")
                    continue

                rtype: str = res.get("ResourceType", "Unknown")
                rid: str = res.get("PhysicalResourceId", "")
                lrid: str = res.get("LogicalResourceId", "")
                status: str = res.get("ResourceStatus", "")

                normalized: dict[str, Any] = {
                    "id":           rid,
                    "arn":          rid if rid.startswith("arn:") else "",
                    "name":         lrid,
                    "stack":        sname,
                    "status":       status,
                    "attributes":   res,
                }
                resources.setdefault(rtype, []).append(normalized)

    except Exception as exc:
        errors.append(f"CloudFormation collection failed: {exc}")

    return InfraSnapshot(
        source="cloudformation",
        collected_at=_utc_now(),
        account_id=account_id,
        region=aws_region,
        resources=resources,
        errors=errors,
    )
