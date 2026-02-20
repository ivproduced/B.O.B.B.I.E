from __future__ import annotations

from langchain_aws import ChatBedrock


def create_nova_client() -> ChatBedrock:
    return ChatBedrock(
        model_id="amazon.nova-pro-v1:0",
        model_kwargs={"temperature": 0.0, "max_tokens": 4096, "top_p": 0.9},
    )
