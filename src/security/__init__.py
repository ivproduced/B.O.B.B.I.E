"""Security hardening module for BOBBIE.

Addresses OWASP LLM Top 10 and Agentic Application Top 10 vulnerabilities:
  - LLM01/AA01: Prompt injection defense via input sanitization
  - LLM02/AA05: Insecure output handling via output validation
  - LLM04:      Model DoS via call budget enforcement
  - LLM06:      Sensitive info disclosure warnings + data minimization
  - LLM08/AA02/AA09: Excessive agency via FAIL→PASS override blocks
  - AA03:       Path traversal defense via path validation
  - AA06:       Audit logging for all LLM overrides
"""
from src.security.input_sanitizer import sanitize_prompt_field, validate_allowed_path, sanitize_context_keys
from src.security.output_validator import validate_nova_suggestion, validate_confidence
from src.security.audit_log import AuditLog

__all__ = [
    "sanitize_prompt_field",
    "validate_allowed_path",
    "sanitize_context_keys",
    "validate_nova_suggestion",
    "validate_confidence",
    "AuditLog",
]
