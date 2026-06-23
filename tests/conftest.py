"""Pytest configuration for BOBBIE test suite.

Provides fixtures that ensure test isolation for security-sensitive module-level
globals (LLM budget, audit log) so tests do not interfere with one another.
"""
import pytest

import src.agents.base_family_agent as _bfa
from src.security.audit_log import reset_default_log


@pytest.fixture(autouse=True)
def reset_llm_budget_and_audit_log():
    """Reset the LLM call budget and audit log before every test.

    These are module-level globals shared across the test session.
    Without a reset between tests, a test that consumes the full budget
    would cause subsequent tests (that call assess_control directly without
    going through the orchestrator) to silently skip all Nova invocations.
    """
    _bfa.set_llm_budget(_bfa._LLM_BUDGET_DEFAULT)
    reset_default_log()
    yield
    # No teardown needed – each test starts with a fresh state.
