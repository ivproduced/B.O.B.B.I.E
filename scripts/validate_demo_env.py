from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "NIST_SP-800-53_rev5_catalog.json",
    "NIST_SP-800-53_rev5_LOW-baseline_profile.json",
    "NIST_SP-800-53_rev5_MODERATE-baseline_profile.json",
    "NIST_SP-800-53_rev5_HIGH-baseline_profile.json",
    "NIST_SP-800-53_rev5_PRIVACY-baseline_profile.json",
    "data/demo_frozen/demo_context.json",
]


def _check_dependencies() -> dict[str, Any]:
    deps = {}
    for module_name in ["streamlit", "boto3", "Evtx"]:
        try:
            __import__(module_name)
            deps[module_name] = {"ok": True}
        except Exception as exc:
            deps[module_name] = {"ok": False, "error": str(exc)}
    return deps


def _check_files(repo_root: Path) -> dict[str, Any]:
    out = {}
    for rel in REQUIRED_FILES:
        path = repo_root / rel
        out[rel] = {"ok": path.exists(), "path": str(path)}
    return out


def _check_aws() -> dict[str, Any]:
    result: dict[str, Any] = {
        "credentials_present": False,
        "sts_reachable": False,
        "error": "",
    }

    try:
        import boto3

        session = boto3.Session()
        creds = session.get_credentials()
        result["credentials_present"] = creds is not None

        if creds is None:
            result["error"] = "AWS credentials were not found in environment/profile"
            return result

        sts = session.client("sts")
        identity = sts.get_caller_identity()
        result["sts_reachable"] = True
        result["account"] = identity.get("Account", "")
        result["arn"] = identity.get("Arn", "")
    except Exception as exc:
        result["error"] = str(exc)

    return result


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]

    payload = {
        "repo_root": str(repo_root),
        "files": _check_files(repo_root),
        "dependencies": _check_dependencies(),
        "aws": _check_aws(),
    }

    file_failures = [key for key, item in payload["files"].items() if not item["ok"]]
    dependency_failures = [key for key, item in payload["dependencies"].items() if not item["ok"]]

    payload["summary"] = {
        "file_failures": file_failures,
        "dependency_failures": dependency_failures,
        "aws_credentials_present": payload["aws"].get("credentials_present", False),
        "aws_sts_reachable": payload["aws"].get("sts_reachable", False),
    }

    print(json.dumps(payload, indent=2))

    if file_failures or dependency_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
