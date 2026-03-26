import json
import logging
from collections.abc import Callable
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def _anthropic_to_openai_tool(tool: dict) -> dict:
    """Convert an Anthropic-format tool schema to OpenAI format.

    Anthropic: {"name": ..., "description": ..., "input_schema": {...}}
    OpenAI:    {"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
    """
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool["input_schema"],
        },
    }


def _extraction_tool(response_model: type[BaseModel]) -> dict:
    """Build an OpenAI-format extraction tool from a Pydantic model."""
    schema = response_model.model_json_schema()
    tool_name = f"extract_{response_model.__name__}"
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": f"Extract structured {response_model.__name__} data",
            "parameters": schema,
        },
    }


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
) -> T:
    """Generate a structured response using OpenAI-compatible tool calling.

    Defines a single extraction tool from the Pydantic schema and forces
    the model to call it via tool_choice.
    """
    tool = _extraction_tool(response_model)
    tool_name = tool["function"]["name"]

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                tools=[tool],
                tool_choice={"type": "function", "function": {"name": tool_name}},
            )
            arguments = response.choices[0].message.tool_calls[0].function.arguments
            return response_model.model_validate_json(arguments)
        except Exception:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "Structured LLM call failed (attempt %d/%d)", attempt + 1, max_retries
            )


async def generate_with_tools(
    client: AsyncOpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    tools: list[dict],
    tool_executors: dict[str, Callable],
    response_model: type[T],
    max_retries: int,
    max_iterations: int = 10,
) -> T:
    """Run an agentic tool-use loop, returning a structured response.

    The model can call investigation tools (looked up via *tool_executors*)
    and finishes by calling the extraction tool built from *response_model*.
    Tools are expected in Anthropic format and converted to OpenAI format.
    """
    extraction = _extraction_tool(response_model)
    extraction_tool_name = extraction["function"]["name"]

    openai_tools = [_anthropic_to_openai_tool(t) for t in tools] + [extraction]
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for iteration in range(max_iterations):
        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=openai_tools,
                )
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    "Tool-use LLM call failed (attempt %d/%d)", attempt + 1, max_retries
                )

        message = response.choices[0].message
        # Append assistant message to conversation
        messages.append(message)

        tool_calls = message.tool_calls
        if not tool_calls:
            # No tool calls — force extraction
            logger.debug("No tool calls on iteration %d, forcing extraction", iteration)
            for attempt in range(max_retries):
                try:
                    response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=[extraction],
                        tool_choice={
                            "type": "function",
                            "function": {"name": extraction_tool_name},
                        },
                    )
                    arguments = (
                        response.choices[0].message.tool_calls[0].function.arguments
                    )
                    return response_model.model_validate_json(arguments)
                except Exception:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        "Forced extraction failed (attempt %d/%d)",
                        attempt + 1,
                        max_retries,
                    )

        # Process tool calls
        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            # Extraction tool → parse and return
            if fn_name == extraction_tool_name:
                return response_model.model_validate_json(
                    tool_call.function.arguments
                )
            # Investigation tool → execute and collect result
            executor = tool_executors.get(fn_name)
            if executor is None:
                result_content = f"Error: unknown tool '{fn_name}'"
            else:
                try:
                    args = json.loads(tool_call.function.arguments)
                    result_content = await executor(**args)
                except Exception as exc:
                    result_content = f"Error executing {fn_name}: {exc}"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_content,
                }
            )

    raise RuntimeError(f"generate_with_tools exceeded {max_iterations} iterations")
