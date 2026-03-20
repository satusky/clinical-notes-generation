import json
import logging
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


async def generate(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_retries: int,
) -> str:
    """Generate a free-text response using an OpenAI-compatible API."""
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.warning("LLM call failed (attempt %d/%d)", attempt + 1, max_retries)


async def generate_structured(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    max_retries: int,
    *,
    supports_json_schema: bool = True,
) -> T:
    """Generate a structured response using an OpenAI-compatible API.

    When supports_json_schema is True (OpenAI, vLLM), uses response_format
    with json_schema. When False (Ollama), uses json_object mode with the
    schema injected into the system prompt.
    """
    schema = response_model.model_json_schema()
    schema_name = response_model.__name__

    if supports_json_schema:
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        }
        final_system_prompt = system_prompt
    else:
        # Ollama: json_object mode + schema in prompt
        response_format = {"type": "json_object"}
        final_system_prompt = (
            f"{system_prompt}\n\n"
            f"You MUST respond with valid JSON matching this schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```\n"
            f"Respond ONLY with the JSON object, no other text."
        )

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_format,
            )
            content = response.choices[0].message.content
            return response_model.model_validate_json(content)
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "Structured LLM call failed (attempt %d/%d)", attempt + 1, max_retries
            )
