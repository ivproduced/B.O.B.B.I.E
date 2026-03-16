"""
Terraform state (.tfstate) collector.

Parses a local terraform.tfstate JSON file and normalizes every managed resource
into the standard InfraSnapshot format using a Terraform → CloudFormation type
mapping table.  Unknown resource types are kept under their raw terraform key.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.collectors.base import InfraSnapshot, _utc_now

# ── Terraform resource_type → CloudFormation resource type ──────────────────
TF_TO_CFN: dict[str, str] = {
    # IAM
    "aws_iam_role":                    "AWS::IAM::Role",
    "aws_iam_user":                    "AWS::IAM::User",
    "aws_iam_group":                   "AWS::IAM::Group",
    "aws_iam_policy":                  "AWS::IAM::ManagedPolicy",
    "aws_iam_role_policy":             "AWS::IAM::Policy",
    "aws_iam_user_policy":             "AWS::IAM::Policy",
    "aws_iam_account_password_policy": "AWS::IAM::AccountPasswordPolicy",
    # S3
    "aws_s3_bucket":                              "AWS::S3::Bucket",
    "aws_s3_bucket_public_access_block":          "AWS::S3::Bucket",
    "aws_s3_bucket_versioning":                   "AWS::S3::Bucket",
    "aws_s3_bucket_server_side_encryption_configuration": "AWS::S3::Bucket",
    "aws_s3_bucket_logging":                      "AWS::S3::BucketLogging",
    # CloudTrail
    "aws_cloudtrail": "AWS::CloudTrail::Trail",
    # EC2 / VPC / SG
    "aws_instance":               "AWS::EC2::Instance",
    "aws_security_group":         "AWS::EC2::SecurityGroup",
    "aws_vpc":                    "AWS::EC2::VPC",
    "aws_subnet":                 "AWS::EC2::Subnet",
    "aws_network_acl":            "AWS::EC2::NetworkAcl",
    "aws_internet_gateway":       "AWS::EC2::InternetGateway",
    "aws_route_table":            "AWS::EC2::RouteTable",
    # RDS
    "aws_db_instance":          "AWS::RDS::DBInstance",
    "aws_db_cluster":           "AWS::RDS::DBCluster",
    # KMS
    "aws_kms_key":   "AWS::KMS::Key",
    "aws_kms_alias": "AWS::KMS::Alias",
    # Lambda
    "aws_lambda_function": "AWS::Lambda::Function",
    # ECS / EKS
    "aws_ecs_cluster":   "AWS::ECS::Cluster",
    "aws_ecs_service":   "AWS::ECS::Service",
    "aws_eks_cluster":   "AWS::EKS::Cluster",
    # SSM / Secrets Manager / Config
    "aws_ssm_parameter":              "AWS::SSM::Parameter",
    "aws_secretsmanager_secret":      "AWS::SecretsManager::Secret",
    "aws_config_configuration_recorder": "AWS::Config::ConfigurationRecorder",
    "aws_config_delivery_channel":    "AWS::Config::DeliveryChannel",
    # CloudWatch / GuardDuty / SecurityHub
    "aws_cloudwatch_log_group":    "AWS::Logs::LogGroup",
    "aws_cloudwatch_metric_alarm": "AWS::CloudWatch::Alarm",
    "aws_guardduty_detector":      "AWS::GuardDuty::Detector",
    "aws_securityhub_account":     "AWS::SecurityHub::Hub",
    # SNS / SQS
    "aws_sns_topic": "AWS::SNS::Topic",
    "aws_sqs_queue": "AWS::SQS::Queue",
    # ELB
    "aws_lb":          "AWS::ElasticLoadBalancingV2::LoadBalancer",
    "aws_alb":         "AWS::ElasticLoadBalancingV2::LoadBalancer",
    "aws_elb":         "AWS::ElasticLoadBalancing::LoadBalancer",
    # DynamoDB
    "aws_dynamodb_table": "AWS::DynamoDB::Table",
    # WAF
    "aws_wafv2_web_acl": "AWS::WAFv2::WebACL",
}


def _normalize_resource(tf_type: str, instance: dict[str, Any], module_path: str = "") -> dict[str, Any]:
    attrs = instance.get("attributes", {})
    resource_id = (
        attrs.get("id")
        or attrs.get("arn")
        or attrs.get("name")
        or instance.get("id", "unknown")
    )
    return {
        "id":         resource_id,
        "arn":        attrs.get("arn", ""),
        "name":       attrs.get("name") or attrs.get("id", ""),
        "module":     module_path,
        "attributes": attrs,
    }


def collect(
    infra_file: str | None,
    region: str = "us-east-1",
) -> InfraSnapshot:
    errors: list[str] = []
    resources: dict[str, list[dict[str, Any]]] = {}

    if not infra_file:
        return InfraSnapshot(
            source="terraform",
            collected_at=_utc_now(),
            account_id="unknown",
            region=region,
            resources={},
            errors=["No terraform state file provided. Pass --infra-file path/to/terraform.tfstate"],
        )

    state_path = Path(infra_file)
    if not state_path.exists():
        return InfraSnapshot(
            source="terraform",
            collected_at=_utc_now(),
            account_id="unknown",
            region=region,
            resources={},
            errors=[f"Terraform state file not found: {state_path}"],
        )

    try:
        state: dict[str, Any] = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return InfraSnapshot(
            source="terraform",
            collected_at=_utc_now(),
            account_id="unknown",
            region=region,
            resources={},
            errors=[f"Failed to parse terraform state: {exc}"],
        )

    # Support both tfstate v3 (modules[].resources) and v4 (resources[])
    raw_resources: list[dict[str, Any]] = []

    if state.get("version", 0) >= 4:
        raw_resources = state.get("resources", [])
    else:
        for module in state.get("modules", []):
            for res_key, res_val in module.get("resources", {}).items():
                raw_resources.append({
                    "type":      res_val.get("type", ""),
                    "name":      res_val.get("primary", {}).get("id", res_key),
                    "module":    module.get("path", ["root"])[-1],
                    "instances": [{"attributes": res_val.get("primary", {}).get("attributes", {})}],
                })

    account_id = "unknown"

    for res in raw_resources:
        tf_type: str = res.get("type", "")
        module_path: str = res.get("module", "root")

        # skip data sources
        if res.get("mode") == "data":
            continue

        cfn_type = TF_TO_CFN.get(tf_type, f"Terraform::{tf_type}")

        for instance in res.get("instances", []):
            normalized = _normalize_resource(tf_type, instance, module_path)
            resources.setdefault(cfn_type, []).append(normalized)

            # try to extract account id from an ARN
            if account_id == "unknown" and normalized.get("arn"):
                parts = str(normalized["arn"]).split(":")
                if len(parts) >= 5 and parts[4]:
                    account_id = parts[4]

    return InfraSnapshot(
        source="terraform",
        collected_at=_utc_now(),
        account_id=account_id,
        region=region,
        resources=resources,
        raw=state,
        errors=errors,
    )
