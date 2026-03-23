"""LLM abstraction layer with native OpenAI and Anthropic SDK support.

Supports providers: openai/, anthropic/, ollama/, vllm/
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from ..config import settings
from ._types import Provider, parse_model

if TYPE_CHECKING:
    from anthropic import AsyncAnthropic
    from openai import AsyncOpenAI

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# Lazy-initialized clients
_openai_clients: dict[str, AsyncOpenAI] = {}
_anthropic_client: AsyncAnthropic | None = None


def _get_openai_client(provider: Provider) -> "AsyncOpenAI":
    """Get or create an AsyncOpenAI client for the given provider."""
    from openai import AsyncOpenAI

    key = provider.value
    if key not in _openai_clients:
        if provider == Provider.OPENAI:
            _openai_clients[key] = AsyncOpenAI(api_key=settings.openai_api_key)
        elif provider == Provider.OLLAMA:
            _openai_clients[key] = AsyncOpenAI(
                base_url=settings.ollama_base_url,
                api_key="ollama",  # Ollama doesn't require a real key
            )
        elif provider == Provider.VLLM:
            _openai_clients[key] = AsyncOpenAI(
                base_url=settings.vllm_base_url,
                api_key="vllm",  # vLLM doesn't require a real key by default
            )
    return _openai_clients[key]


def _get_anthropic_client() -> "AsyncAnthropic":
    """Get or create an AsyncAnthropic client."""
    from anthropic import AsyncAnthropic

    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


async def generate(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    """Generate a free-text response from the LLM."""
    model = model or settings.default_model
    provider, model_name = parse_model(model)

    if provider == Provider.ANTHROPIC:
        from . import _anthropic

        client = _get_anthropic_client()
        return await _anthropic.generate(
            client, model_name, system_prompt, user_prompt, settings.max_retries
        )
    else:
        from . import _openai

        client = _get_openai_client(provider)
        return await _openai.generate(
            client, model_name, system_prompt, user_prompt, settings.max_retries
        )


async def generate_structured(
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    model: str | None = None,
) -> T:
    """Generate a structured (Pydantic-validated) response from the LLM."""
    model = model or settings.default_model
    provider, model_name = parse_model(model)

    if provider == Provider.ANTHROPIC:
        from . import _anthropic

        client = _get_anthropic_client()
        return await _anthropic.generate_structured(
            client, model_name, system_prompt, user_prompt, response_model, settings.max_retries
        )
    else:
        from . import _openai

        client = _get_openai_client(provider)
        supports_json_schema = provider != Provider.OLLAMA
        return await _openai.generate_structured(
            client,
            model_name,
            system_prompt,
            user_prompt,
            response_model,
            settings.max_retries,
            supports_json_schema=supports_json_schema,
        )


async def generate_with_tools(
    system_prompt: str,
    user_prompt: str,
    tools: list[dict],
    tool_executors: dict[str, Callable],
    response_model: type[T],
    model: str | None = None,
    max_iterations: int = 10,
) -> T:
    """Run an agentic tool-use loop, returning a structured response.

    Currently only supported for Anthropic models.
    """
    model = model or settings.default_model
    provider, model_name = parse_model(model)

    if provider == Provider.ANTHROPIC:
        from . import _anthropic

        client = _get_anthropic_client()
        return await _anthropic.generate_with_tools(
            client,
            model_name,
            system_prompt,
            user_prompt,
            tools,
            tool_executors,
            response_model,
            settings.max_retries,
            max_iterations=max_iterations,
        )
    else:
        raise NotImplementedError(
            f"generate_with_tools is not supported for provider '{provider.value}'. "
            "Use generate_structured as a fallback."
        )
