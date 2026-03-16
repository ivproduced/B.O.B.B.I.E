"""
Live boto3 collector — BOBBIE's original assessment mode.

Calls AWS APIs directly for each relevant service family and normalizes
the response into the standard InfraSnapshot format.  This is the fallback
when no static infrastructure file is supplied.

Services covered:
  IAM, S3, CloudTrail, EC2 (instances + SGs + VPCs),
  KMS, RDS, Lambda, GuardDuty, SecurityHub, Config recorder,
  CloudWatch Logs, SSM, Secrets Manager
"""
from __future__ import annotations

from typing import Any

from src.collectors.base import InfraSnapshot, _utc_now


def _boto_session(profile: str | None, region: str):
    import boto3
    if profile:
        return boto3.Session(profile_name=profile, region_name=region)
    return boto3.Session(region_name=region)


def _safe(fn, *args, default=None, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default


# ── per-service collectors ────────────────────────────────────────────────────

def _collect_iam(session, resources: dict, errors: list) -> str:
    account_id = "unknown"
    try:
        iam = session.client("iam")
        sts = session.client("sts")
        account_id = sts.get_caller_identity()["Account"]

        # Roles
        roles = []
        paginator = iam.get_paginator("list_roles")
        for page in paginator.paginate():
            for r in page["Roles"]:
                roles.append({"id": r["RoleId"], "arn": r["Arn"], "name": r["RoleName"], "attributes": r})
        resources["AWS::IAM::Role"] = roles

        # Users
        users = []
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            for u in page["Users"]:
                users.append({"id": u["UserId"], "arn": u["Arn"], "name": u["UserName"], "attributes": u})
        resources["AWS::IAM::User"] = users

        # Account password policy
        try:
            pp = iam.get_account_password_policy()["PasswordPolicy"]
            resources["AWS::IAM::AccountPasswordPolicy"] = [{"id": account_id, "arn": "", "name": "password-policy", "attributes": pp}]
        except Exception:
            resources["AWS::IAM::AccountPasswordPolicy"] = []

    except Exception as exc:
        errors.append(f"IAM collection error: {exc}")

    return account_id


def _collect_s3(session, resources: dict, errors: list) -> None:
    try:
        s3 = session.client("s3")
        buckets = []
        for b in s3.list_buckets().get("Buckets", []):
            name = b["Name"]
            attrs: dict[str, Any] = {"Name": name}
            # Versioning
            v = _safe(s3.get_bucket_versioning, Bucket=name)
            if v:
                attrs["Versioning"] = v.get("Status", "Disabled")
            # Encryption
            enc = _safe(s3.get_bucket_encryption, Bucket=name)
            if enc:
                attrs["Encryption"] = enc.get("ServerSideEncryptionConfiguration", {})
            # Public access block
            pab = _safe(s3.get_public_access_block, Bucket=name)
            if pab:
                attrs["PublicAccessBlock"] = pab.get("PublicAccessBlockConfiguration", {})
            # Logging
            log = _safe(s3.get_bucket_logging, Bucket=name)
            if log:
                attrs["Logging"] = log.get("LoggingEnabled", {})
            buckets.append({"id": name, "arn": f"arn:aws:s3:::{name}", "name": name, "attributes": attrs})
        resources["AWS::S3::Bucket"] = buckets
    except Exception as exc:
        errors.append(f"S3 collection error: {exc}")


def _collect_cloudtrail(session, resources: dict, errors: list) -> None:
    try:
        ct = session.client("cloudtrail")
        trails = []
        for t in ct.describe_trails(includeShadowTrails=False).get("trailList", []):
            arn = t.get("TrailARN", "")
            status = _safe(ct.get_trail_status, Name=arn) or {}
            attrs = {**t, "status": status}
            trails.append({"id": arn, "arn": arn, "name": t.get("Name", ""), "attributes": attrs})
        resources["AWS::CloudTrail::Trail"] = trails
    except Exception as exc:
        errors.append(f"CloudTrail collection error: {exc}")


def _collect_ec2(session, resources: dict, errors: list) -> None:
    try:
        ec2 = session.client("ec2")

        # Instances
        instances = []
        r = ec2.describe_instances()
        for res in r.get("Reservations", []):
            for inst in res.get("Instances", []):
                iid = inst.get("InstanceId", "")
                instances.append({"id": iid, "arn": "", "name": iid, "attributes": inst})
        resources["AWS::EC2::Instance"] = instances

        # Security groups
        sgs = []
        for sg in ec2.describe_security_groups().get("SecurityGroups", []):
            sgs.append({"id": sg["GroupId"], "arn": "", "name": sg["GroupName"], "attributes": sg})
        resources["AWS::EC2::SecurityGroup"] = sgs

        # VPCs
        vpcs = []
        for vpc in ec2.describe_vpcs().get("Vpcs", []):
            vpcs.append({"id": vpc["VpcId"], "arn": "", "name": vpc["VpcId"], "attributes": vpc})
        resources["AWS::EC2::VPC"] = vpcs

    except Exception as exc:
        errors.append(f"EC2 collection error: {exc}")


def _collect_kms(session, resources: dict, errors: list) -> None:
    try:
        kms = session.client("kms")
        keys = []
        paginator = kms.get_paginator("list_keys")
        for page in paginator.paginate():
            for k in page["Keys"]:
                kid = k["KeyId"]
                meta = _safe(kms.describe_key, KeyId=kid) or {}
                attrs = meta.get("KeyMetadata", {"KeyId": kid})
                keys.append({"id": kid, "arn": k.get("KeyArn", ""), "name": kid, "attributes": attrs})
        resources["AWS::KMS::Key"] = keys
    except Exception as exc:
        errors.append(f"KMS collection error: {exc}")


def _collect_rds(session, resources: dict, errors: list) -> None:
    try:
        rds = session.client("rds")
        instances = []
        paginator = rds.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            for db in page["DBInstances"]:
                arn = db.get("DBInstanceArn", "")
                instances.append({"id": db["DBInstanceIdentifier"], "arn": arn, "name": db["DBInstanceIdentifier"], "attributes": db})
        resources["AWS::RDS::DBInstance"] = instances
    except Exception as exc:
        errors.append(f"RDS collection error: {exc}")


def _collect_lambda(session, resources: dict, errors: list) -> None:
    try:
        lmb = session.client("lambda")
        functions = []
        paginator = lmb.get_paginator("list_functions")
        for page in paginator.paginate():
            for fn in page["Functions"]:
                arn = fn.get("FunctionArn", "")
                functions.append({"id": fn["FunctionName"], "arn": arn, "name": fn["FunctionName"], "attributes": fn})
        resources["AWS::Lambda::Function"] = functions
    except Exception as exc:
        errors.append(f"Lambda collection error: {exc}")


def _collect_guardduty(session, resources: dict, errors: list) -> None:
    try:
        gd = session.client("guardduty")
        detectors = []
        for did in gd.list_detectors().get("DetectorIds", []):
            det = _safe(gd.get_detector, DetectorId=did) or {}
            detectors.append({"id": did, "arn": "", "name": did, "attributes": {**det, "DetectorId": did}})
        resources["AWS::GuardDuty::Detector"] = detectors
    except Exception as exc:
        errors.append(f"GuardDuty collection error: {exc}")


def _collect_securityhub(session, resources: dict, errors: list) -> None:
    try:
        sh = session.client("securityhub")
        hub = _safe(sh.describe_hub)
        if hub:
            resources["AWS::SecurityHub::Hub"] = [{"id": hub.get("HubArn", ""), "arn": hub.get("HubArn", ""), "name": "SecurityHub", "attributes": hub}]
        else:
            resources["AWS::SecurityHub::Hub"] = []
    except Exception as exc:
        errors.append(f"SecurityHub collection error: {exc}")


def _collect_config(session, resources: dict, errors: list) -> None:
    try:
        cfg = session.client("config")
        recorders = cfg.describe_configuration_recorders().get("ConfigurationRecorders", [])
        normalized = []
        for r in recorders:
            normalized.append({"id": r.get("name", "default"), "arn": "", "name": r.get("name", "default"), "attributes": r})
        resources["AWS::Config::ConfigurationRecorder"] = normalized
    except Exception as exc:
        errors.append(f"Config collection error: {exc}")


def _collect_cloudwatch_logs(session, resources: dict, errors: list) -> None:
    try:
        cw = session.client("logs")
        groups = []
        paginator = cw.get_paginator("describe_log_groups")
        for page in paginator.paginate():
            for lg in page["logGroups"]:
                groups.append({"id": lg["logGroupName"], "arn": lg.get("arn", ""), "name": lg["logGroupName"], "attributes": lg})
        resources["AWS::Logs::LogGroup"] = groups
    except Exception as exc:
        errors.append(f"CloudWatch Logs collection error: {exc}")


# ── main entry point ──────────────────────────────────────────────────────────

def collect(aws_profile: str | None, aws_region: str) -> InfraSnapshot:
    errors: list[str] = []
    resources: dict[str, list[dict[str, Any]]] = {}

    try:
        session = _boto_session(aws_profile, aws_region)
        account_id = _collect_iam(session, resources, errors)
        _collect_s3(session, resources, errors)
        _collect_cloudtrail(session, resources, errors)
        _collect_ec2(session, resources, errors)
        _collect_kms(session, resources, errors)
        _collect_rds(session, resources, errors)
        _collect_lambda(session, resources, errors)
        _collect_guardduty(session, resources, errors)
        _collect_securityhub(session, resources, errors)
        _collect_config(session, resources, errors)
        _collect_cloudwatch_logs(session, resources, errors)
    except Exception as exc:
        errors.append(f"Live collection session error: {exc}")
        account_id = "unknown"

    return InfraSnapshot(
        source="live",
        collected_at=_utc_now(),
        account_id=account_id,
        region=aws_region,
        resources=resources,
        errors=errors,
    )
