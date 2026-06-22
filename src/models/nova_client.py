"""Backwards-compatible shim — delegates to the provider-agnostic llm_factory."""
from __future__ import annotations

from typing import Any

from src.models.llm_factory import create_llm_client


def create_nova_client(region_name: str | None = None) -> Any:
    """Deprecated shim — use src.models.llm_factory.create_llm_client instead."""
    ctx: dict[str, Any] = {}
    if region_name:
        ctx["llm_aws_region"] = region_name
    return create_llm_client(ctx)
