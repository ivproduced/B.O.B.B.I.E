"""LLM output validation for Nova Pro responses.

Addresses:
  - LLM02/AA05: Insecure output handling – LLM-returned values used without validation
  - LLM08/AA02: Excessive agency – Nova cannot auto-promote FAIL→PASS
"""
from __future__ import annotations

from typing import Any

# Allowlists for LLM-returned classification values.
_VALID_STATUSES: frozenset[str] = frozenset({"PASS", "FAIL"})
_VALID_RISK_LEVELS: frozenset[str] = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})


def validate_confidence(raw: Any) -> float:
    """Clamp and coerce a raw confidence value to [0.0, 1.0].

    LLM-returned confidence values must never be trusted at face value;
    an adversarially-crafted response could return confidence=99.9 to
    bypass a threshold gate.
    """
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def validate_nova_suggestion(
    suggestion: dict[str, Any],
    current_status: str,
) -> dict[str, Any]:
    """Validate and normalise a Nova suggestion dict before it may be applied.

    Rules enforced (LLM08/AA02 – Excessive Agency):

    1. ``suggested_status`` must be in the allowlist {PASS, FAIL}. Unknown
       values are nullified so the suggestion cannot be applied.
    2. ``suggested_risk`` must be in the allowlist {LOW, MEDIUM, HIGH, CRITICAL}.
    3. ``confidence`` is clamped to [0.0, 1.0] regardless of what the LLM returned.
    4. **Nova can NEVER auto-promote a FAIL→PASS**. The deterministic assessment
       is the authoritative compliance record; an LLM cannot unilaterally clear
       a compliance failure. The ``suggested_status`` is overridden to ``None``
       when the LLM would change FAIL to PASS, preventing silent compliance bypass.

    Returns a sanitized copy of *suggestion*.
    """
    result = dict(suggestion)

    # 1. Validate suggested_status.
    raw_status = str(result.get("suggested_status") or "").strip().upper()
    if raw_status not in _VALID_STATUSES:
        result["suggested_status"] = None
        result["_validation_note"] = f"suggested_status '{raw_status}' is not in allowlist {_VALID_STATUSES}; nullified."
    else:
        result["suggested_status"] = raw_status

    # 2. Validate suggested_risk.
    raw_risk = str(result.get("suggested_risk") or "").strip().upper()
    if raw_risk not in _VALID_RISK_LEVELS:
        result["suggested_risk"] = None
    else:
        result["suggested_risk"] = raw_risk

    # 3. Clamp confidence.
    result["confidence"] = validate_confidence(result.get("confidence"))

    # 4. Block FAIL→PASS auto-promotion (excessive agency / compliance bypass).
    if (
        str(current_status).upper() == "FAIL"
        and result.get("suggested_status") == "PASS"
    ):
        result["suggested_status"] = None
        # Reject the entire suggestion — an LLM that attempted FAIL→PASS
        # cannot be trusted to correctly classify risk level either.
        result["suggested_risk"] = None
        result["_fail_to_pass_blocked"] = (
            "Nova suggested PASS for a deterministically-FAILED control. "
            "Auto-promotion of FAIL→PASS is prohibited to prevent compliance bypass (LLM08/AA02). "
            "Human review required."
        )

    return result
