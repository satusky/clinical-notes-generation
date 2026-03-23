import logging
from collections.abc import Callable
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


async def generate_with_tools(
    client: AsyncAnthropic,
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
    """
    schema = response_model.model_json_schema()
    extraction_tool_name = f"extract_{response_model.__name__}"
    extraction_tool = {
        "name": extraction_tool_name,
        "description": f"Extract structured {response_model.__name__} data",
        "input_schema": schema,
    }

    all_tools = tools + [extraction_tool]
    messages: list[dict] = [{"role": "user", "content": user_prompt}]

    for iteration in range(max_iterations):
        for attempt in range(max_retries):
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=all_tools,
                )
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    "Tool-use LLM call failed (attempt %d/%d)", attempt + 1, max_retries
                )

        # Append the full assistant response to the conversation
        assistant_content = [
            block if isinstance(block, dict) else block.model_dump()
            for block in response.content
        ]
        messages.append({"role": "assistant", "content": assistant_content})

        # Process tool_use blocks
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            # Extraction tool → parse and return
            if block.name == extraction_tool_name:
                return response_model.model_validate(block.input)
            # Investigation tool → execute and collect result
            executor = tool_executors.get(block.name)
            if executor is None:
                result_content = f"Error: unknown tool '{block.name}'"
            else:
                try:
                    result_content = await executor(**block.input)
                except Exception as exc:
                    result_content = f"Error executing {block.name}: {exc}"
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            continue

        # No tool calls (stop_reason == end_turn) → force extraction
        logger.debug("No tool calls on iteration %d, forcing extraction", iteration)
        for attempt in range(max_retries):
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=[extraction_tool],
                    tool_choice={"type": "tool", "name": extraction_tool_name},
                )
                for block in response.content:
                    if block.type == "tool_use":
                        return response_model.model_validate(block.input)
                raise ValueError("No tool_use block in forced extraction response")
            except Exception:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    "Forced extraction failed (attempt %d/%d)", attempt + 1, max_retries
                )

    raise RuntimeError(f"generate_with_tools exceeded {max_iterations} iterations")
