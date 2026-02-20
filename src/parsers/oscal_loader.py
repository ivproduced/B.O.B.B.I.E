from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.models.baseline_profile import BaselineProfile


def _normalize_control_id(control_id: str) -> str:
    normalized = control_id.strip().lower()
    return normalized.replace("(", ".").replace(")", "")


def _tag_membership(control_id: str, baselines: dict[str, BaselineProfile]) -> dict[str, bool]:
    normalized_id = _normalize_control_id(control_id)
    return {
        key: normalized_id in set(profile.selected_control_ids)
        for key, profile in baselines.items()
    }


def load_catalog_and_tag_baselines(
    catalog_path: str,
    baselines: dict[str, BaselineProfile],
) -> dict[str, Any]:
    catalog_json = json.loads(Path(catalog_path).read_text(encoding="utf-8"))

    groups = catalog_json.get("catalog", {}).get("groups", [])
    for group in groups:
        for control in group.get("controls", []):
            control["baselines"] = _tag_membership(control.get("id", ""), baselines)

            for enhancement in control.get("controls", []):
                enhancement["baselines"] = _tag_membership(enhancement.get("id", ""), baselines)

    return catalog_json
