#!/usr/bin/env python3
"""Validate the canonical demo plan against the family registry.
Exits with non-zero code on validation failure.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.demo_plan import DEMO_PLAN
from src.agents.family_registry import validate_plan_vs_registry

try:
    validate_plan_vs_registry(DEMO_PLAN)
    print("Plan validation OK")
    sys.exit(0)
except Exception as e:
    print(f"Plan validation failed: {e}")
    sys.exit(2)
