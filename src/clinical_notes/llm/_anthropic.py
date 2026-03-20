import logging
from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


async def generate(
    client: AsyncAnthropic,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_retries: int,
) -> str:
    """Generate a free-text response using the Anthropic API."""
    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.warning("LLM call failed (attempt %d/%d)", attempt + 1, max_retries)


async def generate_structured(
    client: AsyncAnthropic,
    model: str,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
    max_retries: int,
) -> T:
    """Generate a structured response using Anthropic's tool use.

    Defines a single tool from the Pydantic schema and forces the model
    to call it via tool_choice.
    """
    schema = response_model.model_json_schema()
    tool_name = f"extract_{response_model.__name__}"

    tool = {
        "name": tool_name,
        "description": f"Extract structured {response_model.__name__} data",
        "input_schema": schema,
    }

    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[tool],
                tool_choice={"type": "tool", "name": tool_name},
            )
            # Find the tool_use block in the response
            for block in response.content:
                if block.type == "tool_use":
                    return response_model.model_validate(block.input)
            raise ValueError("No tool_use block in response")
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "Structured LLM call failed (attempt %d/%d)", attempt + 1, max_retries
            )
