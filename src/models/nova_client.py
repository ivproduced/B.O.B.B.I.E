from __future__ import annotations

import os

from langchain_aws import ChatBedrock


def create_nova_client(region_name: str | None = None) -> ChatBedrock:
    region = (
        region_name
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )
    return ChatBedrock(
        model_id="amazon.nova-2-lite-v1:0",
        region_name=region,
        model_kwargs={"temperature": 0.0, "max_tokens": 4096},
    )
