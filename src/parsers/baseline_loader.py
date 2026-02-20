from __future__ import annotations

import json
from pathlib import Path

from src.models.baseline_profile import BaselineProfile


def _normalize_control_id(control_id: str) -> str:
    normalized = control_id.strip().lower()
    return normalized.replace("(", ".").replace(")", "")


def _extract_catalog_control_map(catalog_json: dict) -> dict[str, str]:
    catalog = catalog_json.get("catalog", {})
    control_map: dict[str, str] = {}

    for control in catalog.get("controls", []):
        control_id = _normalize_control_id(control.get("id", ""))
        if control_id:
            control_map[control_id] = control_id
        for enhancement in control.get("controls", []):
            enhancement_id = _normalize_control_id(enhancement.get("id", ""))
            if enhancement_id:
                control_map[enhancement_id] = enhancement_id

    for group in catalog.get("groups", []):
        for control in group.get("controls", []):
            control_id = _normalize_control_id(control.get("id", ""))
            if control_id:
                control_map[control_id] = control_id
            for enhancement in control.get("controls", []):
                enhancement_id = _normalize_control_id(enhancement.get("id", ""))
                if enhancement_id:
                    control_map[enhancement_id] = enhancement_id

    return control_map


def load_baseline_profile(
    profile_path: str,
    catalog_path: str,
    baseline_id: str,
    title: str,
) -> BaselineProfile:
    profile_json = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    catalog_json = json.loads(Path(catalog_path).read_text(encoding="utf-8"))

    control_map = _extract_catalog_control_map(catalog_json)

    imports = profile_json.get("profile", {}).get("imports", [])
    included_ids: set[str] = set()
    for imported in imports:
        for include in imported.get("include-controls", []):
            for with_id in include.get("with-ids", []):
                included_ids.add(_normalize_control_id(str(with_id)))

    selected_control_ids = sorted(control_id for control_id in included_ids if control_id in control_map)

    return BaselineProfile(
        id=baseline_id,
        title=title,
        selected_control_ids=selected_control_ids,
    )


def load_standard_baselines(repo_root: str) -> dict[str, BaselineProfile]:
    root = Path(repo_root)
    catalog_path = str(root / "NIST_SP-800-53_rev5_catalog.json")

    return {
        "LOW": load_baseline_profile(
            profile_path=str(root / "NIST_SP-800-53_rev5_LOW-baseline_profile.json"),
            catalog_path=catalog_path,
            baseline_id="low",
            title="NIST SP 800-53 Rev5 Low Baseline",
        ),
        "MODERATE": load_baseline_profile(
            profile_path=str(root / "NIST_SP-800-53_rev5_MODERATE-baseline_profile.json"),
            catalog_path=catalog_path,
            baseline_id="moderate",
            title="NIST SP 800-53 Rev5 Moderate Baseline",
        ),
        "HIGH": load_baseline_profile(
            profile_path=str(root / "NIST_SP-800-53_rev5_HIGH-baseline_profile.json"),
            catalog_path=catalog_path,
            baseline_id="high",
            title="NIST SP 800-53 Rev5 High Baseline",
        ),
        "PRIVACY": load_baseline_profile(
            profile_path=str(root / "NIST_SP-800-53_rev5_PRIVACY-baseline_profile.json"),
            catalog_path=catalog_path,
            baseline_id="privacy",
            title="NIST SP 800-53 Rev5 Privacy Baseline",
        ),
    }
