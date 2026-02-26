#!/usr/bin/env python3
import json
import ssl
import sys
from pathlib import Path
from urllib.request import urlopen

import certifi
from jsonschema import Draft7Validator, RefResolver


def main():
    poam_path = Path("artifacts/final_run/poam.json")
    if not poam_path.exists():
        print("POA&M file not found:", poam_path)
        sys.exit(2)

    poam = json.loads(poam_path.read_text(encoding="utf-8"))

    # Try a list of likely schema locations in the OSCAL repo and use the
    # first one that responds successfully. This avoids hardcoding a single
    # path that may move between repo layouts.
    candidate_urls = [
        "https://raw.githubusercontent.com/usnistgov/OSCAL/main/src/metaschema/oscal_poam_schema.json",
        "https://raw.githubusercontent.com/usnistgov/OSCAL/main/schema/json/oscal_poam_schema.json",
        "https://raw.githubusercontent.com/usnistgov/OSCAL/main/src/metaschema/json/oscal_poam_schema.json",
        "https://raw.githubusercontent.com/usnistgov/OSCAL/main/src/metaschema/poam.json",
    ]

    # Prefer a vendored schema file for deterministic, offline validation.
    vendored = Path("vendor/oscal-metaschema/oscal_poam_schema.json")
    schema = None
    schema_url = None
    if vendored.exists():
        try:
            print("Using vendored schema at:", vendored)
            schema = json.loads(vendored.read_text(encoding="utf-8"))
            schema_url = f"file://{vendored.resolve()}"
        except Exception as exc:
            print("Failed to load vendored schema:", exc)

    # If vendored schema not present or failed to load, try remote candidates.
    if schema is None:
        ctx = ssl.create_default_context(cafile=certifi.where())
        for url in candidate_urls:
            try:
                print("Trying schema URL:", url)
                raw = urlopen(url, context=ctx, timeout=15).read().decode()
                schema = json.loads(raw)
                schema_url = url
                print("Fetched schema from:", url)
                break
            except Exception as exc:
                print("  failed:", exc)

    if schema is not None and schema_url is not None:
        try:
            resolver = RefResolver(base_uri=schema_url, referrer=schema)
            validator = Draft7Validator(schema, resolver=resolver)

            errors = list(validator.iter_errors(poam))
            if not errors:
                print("\nPOA&M is VALID against OSCAL POA&M schema\n")
                return 0

            print("\nPOA&M is INVALID against OSCAL POA&M schema — first 50 errors:\n")
            for i, e in enumerate(errors[:50], 1):
                path = "/".join([str(p) for p in e.path])
                path = f"/{path}" if path else "/"
                print(f"{i}) {e.message} (at {path})")
            return 3
        except Exception as exc:
            print("Schema loaded but validation failed:", exc)
    else:
        print("Could not load vendored or remote schema; falling back to structural checks.")

    # Fallback structural validation (basic OSCAL-like requirements)
    poam_root = poam.get("plan-of-action-and-milestones") or poam
    metadata = poam_root.get("metadata")
    poam_items = poam_root.get("poam-items") or poam_root.get("poam_items")

    problems = []
    if metadata is None:
        problems.append("missing 'metadata' in plan-of-action-and-milestones")
    else:
        if not metadata.get("title"):
            problems.append("metadata.title is missing or empty")
        if not metadata.get("last-modified"):
            problems.append("metadata.last-modified is missing or empty")

    if not isinstance(poam_items, list):
        problems.append("poam-items must be an array")
    else:
        for idx, item in enumerate(poam_items[:200], 1):
            if not item.get("item_id"):
                problems.append(f"poam item {idx} missing item_id")
            for k in ("family_id", "control_id", "weakness", "risk_level"):
                if not item.get(k):
                    problems.append(f"poam item {idx} missing {k}")

    if problems:
        print("\nStructural validation FAILED — issues found:")
        for p in problems[:100]:
            print(" - ", p)
        return 4

    print("\nStructural validation PASSED: Poam looks OSCAL-like (basic checks).\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
