"""Input sanitization for LLM prompt construction and path handling.

Addresses:
  - LLM01/AA01: Prompt injection – user-controlled values embedded in prompts
  - AA03:       Path traversal – user-supplied paths resolved against repo root
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# ── Prompt injection defense ────────────────────────────────────────────────

# Patterns that attempt to hijack the LLM's role or escape the intended prompt.
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a\s+|an\s+)?(?!federal|security|compliance|analyst|engineer|officer)", re.IGNORECASE),
    re.compile(r"new\s+instruction[s]?[:\s]", re.IGNORECASE),
    re.compile(r"system\s*prompt[:\s]", re.IGNORECASE),
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]|\[SYS\]|\[/SYS\]", re.IGNORECASE),
    re.compile(r"###\s*(instruction|system|human|assistant)\s*:", re.IGNORECASE),
]

# Maximum character length for any single user-controlled field in a prompt.
_MAX_FIELD_LEN = 2000

# Maximum combined character length of the findings list embedded in a prompt.
_MAX_FINDINGS_TOTAL_LEN = 4000


def _fit_truncation_note(value: str, field_name: str, max_len: int) -> str:
    """Truncate *value* so any truncation note still fits within *max_len*."""
    if max_len <= 0:
        return ""

    note = f"… [truncated – original {field_name} exceeded {max_len} chars]"
    if len(note) >= max_len:
        return note[:max_len]

    return value[: max_len - len(note)] + note


def sanitize_prompt_field(value: str, field_name: str = "field", max_len: int = _MAX_FIELD_LEN) -> str:
    """Sanitize a user-controlled string before embedding it in an LLM prompt.

    - Caps the final output at *max_len* characters.
    - Strips injection-attempt patterns (replaces with a safe placeholder).
    - Returns a clean string safe for prompt interpolation.
    """
    if not isinstance(value, str):
        value = str(value)

    for pattern in _INJECTION_PATTERNS:
        value = pattern.sub(f"[REDACTED-{field_name.upper()}]", value)

    # Hard truncation to avoid token stuffing / context overflow.
    if len(value) > max_len:
        value = _fit_truncation_note(value, field_name, max_len)

    return value


def sanitize_findings_list(findings: list[str], max_total_len: int = _MAX_FINDINGS_TOTAL_LEN) -> list[str]:
    """Sanitize a list of finding strings for safe prompt embedding.

    Each finding is individually sanitized, and the total character budget
    across all findings is capped at *max_total_len*.
    """
    sanitized: list[str] = []
    total = 0
    for finding in findings:
        clean = sanitize_prompt_field(finding, field_name="finding", max_len=500)
        if total + len(clean) > max_total_len:
            sanitized.append(f"[… {len(findings) - len(sanitized)} additional findings truncated for LLM input]")
            break
        sanitized.append(clean)
        total += len(clean)
    return sanitized


# ── Path traversal defense ───────────────────────────────────────────────────

def validate_allowed_path(
    candidate: str | Path,
    allowed_root: str | Path,
    label: str = "path",
) -> Path:
    """Resolve *candidate* and verify it is within *allowed_root*.

    Raises ``ValueError`` if the resolved path escapes the allowed root.
    This prevents directory traversal attacks via user-supplied ``catalog_path``,
    ``objective_fixture_path``, or ``repo_root`` context keys.
    """
    resolved = Path(str(candidate)).expanduser().resolve()
    root = Path(str(allowed_root)).expanduser().resolve()

    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError(
            f"Security: {label} '{candidate}' resolves to '{resolved}' which is outside "
            f"the allowed root '{root}'. Path traversal attempt rejected."
        )

    return resolved


# ── Context key injection defense ────────────────────────────────────────────

# Keys that must not be overridden by untrusted uploaded data.
_PROTECTED_CONTEXT_KEYS: frozenset[str] = frozenset(
    {
        "apply_nova_suggestions",
        "nova_confidence_threshold",
        "nova_narrative",
        "orchestrator",
        "deterministic_run",
        "repo_root",
    }
)


def sanitize_context_keys(
    incoming: dict[str, Any],
    protected_keys: frozenset[str] = _PROTECTED_CONTEXT_KEYS,
) -> dict[str, Any]:
    """Return a copy of *incoming* with protected keys removed.

    Prevents uploaded frozen datasets or JSON payloads from overriding
    security-critical settings such as ``apply_nova_suggestions`` or
    ``nova_confidence_threshold`` (LLM08/AA02 excessive agency).
    """
    return {k: v for k, v in incoming.items() if k not in protected_keys}
