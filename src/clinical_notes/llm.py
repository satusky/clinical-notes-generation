import json
import logging
from typing import TypeVar

import litellm
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


async def generate(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    """Generate a free-text response from the LLM."""
    model = model or settings.default_model
    for attempt in range(settings.max_retries):
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception:
            if attempt == settings.max_retries - 1:
                raise
            logger.warning("LLM call failed (attempt %d/%d)", attempt + 1, settings.max_retries)


async def generate_structured(
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    model: str | None = None,
) -> T:
    """Generate a structured (Pydantic-validated) response from the LLM."""
    model = model or settings.default_model
    schema = response_model.model_json_schema()
    schema_prompt = (
        f"{system_prompt}\n\n"
        f"You MUST respond with valid JSON matching this schema:\n"
        f"```json\n{json.dumps(schema, indent=2)}\n```\n"
        f"Respond ONLY with the JSON object, no other text."
    )
    for attempt in range(settings.max_retries):
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": schema_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            return response_model.model_validate_json(content)
        except Exception:
            if attempt == settings.max_retries - 1:
                raise
            logger.warning(
                "Structured LLM call failed (attempt %d/%d)", attempt + 1, settings.max_retries
            )
