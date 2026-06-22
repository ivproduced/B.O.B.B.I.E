"""Structured audit log for LLM override events.

Addresses:
  - AA06: Insufficient logging – LLM overrides of deterministic results must be
    recorded in a tamper-evident, append-only audit trail.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any


class AuditLog:
    """Thread-safe, in-memory append-only audit log for LLM interaction events.

    Events are written for:
      - Nova suggestion application (status/risk override)
      - Blocked FAIL→PASS promotion attempts
      - LLM call budget exhaustion

    The log is included in the assessment result under ``_audit_log`` so it
    travels with the report and can be inspected by reviewers.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[dict[str, Any]] = []

    def _append(self, event_type: str, payload: dict[str, Any]) -> None:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **payload,
        }
        with self._lock:
            self._entries.append(entry)

    def log_nova_suggestion_applied(
        self,
        control_id: str,
        original_status: str,
        new_status: str | None,
        original_risk: str,
        new_risk: str | None,
        confidence: float,
        explanation: str,
    ) -> None:
        """Record when a Nova suggestion is applied to override a deterministic result."""
        self._append(
            "NOVA_SUGGESTION_APPLIED",
            {
                "control_id": control_id,
                "original_status": original_status,
                "new_status": new_status,
                "original_risk": original_risk,
                "new_risk": new_risk,
                "confidence": confidence,
                "explanation": explanation,
            },
        )

    def log_fail_to_pass_blocked(
        self,
        control_id: str,
        confidence: float,
        explanation: str,
    ) -> None:
        """Record a blocked attempt by Nova to promote a FAIL control to PASS."""
        self._append(
            "FAIL_TO_PASS_BLOCKED",
            {
                "control_id": control_id,
                "confidence": confidence,
                "explanation": explanation,
                "reason": "Auto-promotion of FAIL→PASS is prohibited (LLM08/AA02). Human review required.",
            },
        )

    def log_llm_budget_exceeded(self, control_id: str, budget: int) -> None:
        """Record when the per-assessment LLM call budget is exhausted."""
        self._append(
            "LLM_BUDGET_EXCEEDED",
            {
                "control_id": control_id,
                "budget": budget,
                "reason": "Nova invocation skipped: per-assessment LLM call budget exhausted (LLM04).",
            },
        )

    def log_path_traversal_blocked(self, label: str, candidate: str, allowed_root: str) -> None:
        """Record a blocked path traversal attempt."""
        self._append(
            "PATH_TRAVERSAL_BLOCKED",
            {
                "label": label,
                "candidate": candidate,
                "allowed_root": allowed_root,
            },
        )

    def log_context_key_stripped(self, key: str) -> None:
        """Record when a protected context key was stripped from uploaded data."""
        self._append(
            "PROTECTED_CONTEXT_KEY_STRIPPED",
            {
                "key": key,
                "reason": "Uploaded data attempted to override a protected security context key (LLM08/AA02).",
            },
        )

    def entries(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)

    def to_json(self) -> str:
        return json.dumps(self.entries(), indent=2)


# Module-level singleton used across an assessment run.
# The orchestrator resets this per run to avoid cross-run leakage.
_default_log = AuditLog()


def get_default_log() -> AuditLog:
    return _default_log


def reset_default_log() -> AuditLog:
    """Create and install a fresh AuditLog for a new assessment run."""
    global _default_log
    _default_log = AuditLog()
    return _default_log
