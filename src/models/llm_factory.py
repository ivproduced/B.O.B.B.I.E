"""Provider-agnostic LLM factory.

Supported providers (set via LLM_PROVIDER env var or context["llm_provider"]):
  bedrock  – Amazon Bedrock (default, requires AWS credentials)
  openai   – OpenAI or any OpenAI-compatible endpoint (set LLM_BASE_URL to swap)

Environment variables (all optional, context keys override them at call time):
  LLM_PROVIDER      bedrock | openai          (default: bedrock)
  LLM_MODEL_ID      model identifier          (provider-specific defaults below)
  LLM_BASE_URL      base URL for openai-compat endpoints
  LLM_API_KEY       API key for openai-compat endpoints
  LLM_TEMPERATURE   float 0.0–1.0             (default: 0.0)
  LLM_MAX_TOKENS    positive int              (default: 4096)

  # Bedrock-specific
  AWS_REGION / AWS_DEFAULT_REGION             (default: us-east-1)
"""
from __future__ import annotations

import os
from typing import Any


_DEFAULT_MODEL: dict[str, str] = {
    "bedrock": "amazon.nova-2-lite-v1:0",
    "openai": "gpt-4o",
}


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def create_llm_client(context: dict[str, Any] | None = None) -> Any:
    """Return an LLM client with a LangChain-compatible `.invoke()` interface.

    Resolution order for every setting:
      1. context dict (passed at call time)
      2. environment variable
      3. hard-coded default
    """
    ctx = context or {}

    provider = (
        str(ctx.get("llm_provider", "") or "").strip()
        or _env("LLM_PROVIDER")
        or "bedrock"
    ).lower()

    temperature = float(
        ctx.get("llm_temperature")
        or _env("LLM_TEMPERATURE")
        or 0.0
    )
    max_tokens = int(
        ctx.get("llm_max_tokens")
        or _env("LLM_MAX_TOKENS")
        or 4096
    )
    model_id = (
        str(ctx.get("llm_model_id", "") or "").strip()
        or _env("LLM_MODEL_ID")
        or _DEFAULT_MODEL.get(provider, "")
    )

    if provider == "bedrock":
        from langchain_aws import ChatBedrock

        region = (
            str(ctx.get("llm_aws_region") or ctx.get("aws_region", "") or "").strip()
            or _env("AWS_REGION")
            or _env("AWS_DEFAULT_REGION")
            or "us-east-1"
        )
        return ChatBedrock(
            model_id=model_id,
            region_name=region,
            model_kwargs={"temperature": temperature, "max_tokens": max_tokens},
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = (
            str(ctx.get("llm_api_key", "") or "").strip()
            or _env("LLM_API_KEY")
            or _env("OPENAI_API_KEY")
            or "sk-placeholder"
        )
        base_url = (
            str(ctx.get("llm_base_url", "") or "").strip()
            or _env("LLM_BASE_URL")
            or None
        )
        kwargs: dict[str, Any] = {
            "model": model_id,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)

    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        "Supported values: 'bedrock', 'openai'."
    )
