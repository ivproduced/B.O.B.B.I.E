import pytest

from src.config.demo_plan import DEMO_PLAN
from src.agents.family_registry import validate_plan_vs_registry


def test_demo_plan_validates_against_registry():
    # Should not raise
    validate_plan_vs_registry(DEMO_PLAN)


def test_plan_with_unsupported_control_raises():
    # create a plan with an unsupported control PL-9 for PL
    bad_plan = {"PL": ["PL-9"]}
    with pytest.raises(ValueError):
        validate_plan_vs_registry(bad_plan)
