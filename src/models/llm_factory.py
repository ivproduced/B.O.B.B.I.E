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


def _resolve_raw_setting(
    ctx: dict[str, Any],
    context_key: str,
    env_key: str,
    default: Any,
) -> tuple[Any, str]:
    if context_key in ctx and ctx[context_key] is not None:
        return ctx[context_key], context_key
    env_value = _env(env_key)
    if env_value:
        return env_value, env_key
    return default, context_key


def _resolve_float_setting(
    ctx: dict[str, Any],
    context_key: str,
    env_key: str,
    default: float,
    *,
    min_value: float,
) -> float:
    raw_value, source = _resolve_raw_setting(ctx, context_key, env_key, default)
    try:
        value = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid {source} value {raw_value!r}: expected a number."
        ) from exc
    if value < min_value:
        raise ValueError(
            f"Invalid {source} value {raw_value!r}: expected a number >= {min_value}."
        )
    return value


def _resolve_int_setting(
    ctx: dict[str, Any],
    context_key: str,
    env_key: str,
    default: int,
    *,
    min_value: int,
) -> int:
    raw_value, source = _resolve_raw_setting(ctx, context_key, env_key, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid {source} value {raw_value!r}: expected an integer."
        ) from exc
    if value < min_value:
        raise ValueError(
            f"Invalid {source} value {raw_value!r}: expected an integer >= {min_value}."
        )
    return value


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

    temperature = _resolve_float_setting(
        ctx,
        "llm_temperature",
        "LLM_TEMPERATURE",
        0.0,
        min_value=0.0,
    )
    max_tokens = _resolve_int_setting(
        ctx,
        "llm_max_tokens",
        "LLM_MAX_TOKENS",
        4096,
        min_value=1,
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

        base_url = (
            str(ctx.get("llm_base_url", "") or "").strip()
            or _env("LLM_BASE_URL")
            or None
        )
        api_key = (
            str(ctx.get("llm_api_key", "") or "").strip()
            or _env("LLM_API_KEY")
            or _env("OPENAI_API_KEY")
        )
        if not api_key:
            if base_url:
                api_key = "no-key-required"
            else:
                raise ValueError(
                    "An OpenAI API key is required when using the public OpenAI "
                    "endpoint. Set LLM_API_KEY or OPENAI_API_KEY, pass "
                    "llm_api_key, or set LLM_BASE_URL for a local "
                    "OpenAI-compatible server."
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
