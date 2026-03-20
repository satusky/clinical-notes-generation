from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from src.clinical_notes.llm._types import Provider, parse_model


# --- parse_model tests ---


class TestParseModel:
    def test_anthropic(self):
        provider, name = parse_model("anthropic/claude-sonnet-4-20250514")
        assert provider == Provider.ANTHROPIC
        assert name == "claude-sonnet-4-20250514"

    def test_openai(self):
        provider, name = parse_model("openai/gpt-4o")
        assert provider == Provider.OPENAI
        assert name == "gpt-4o"

    def test_ollama(self):
        provider, name = parse_model("ollama/llama3")
        assert provider == Provider.OLLAMA
        assert name == "llama3"

    def test_vllm(self):
        provider, name = parse_model("vllm/mistral-7b")
        assert provider == Provider.VLLM
        assert name == "mistral-7b"

    def test_unknown_prefix(self):
        with pytest.raises(ValueError, match="Unknown provider prefix 'foo'"):
            parse_model("foo/bar")

    def test_no_slash(self):
        with pytest.raises(ValueError, match="provider/model_name"):
            parse_model("just-a-model")

    def test_model_with_slashes(self):
        provider, name = parse_model("openai/org/gpt-4o")
        assert provider == Provider.OPENAI
        assert name == "org/gpt-4o"


# --- Dispatch tests ---


class SampleModel(BaseModel):
    name: str
    value: int


@pytest.mark.asyncio
async def test_generate_dispatches_to_anthropic():
    with (
        patch("src.clinical_notes.llm._anthropic.generate", new_callable=AsyncMock) as mock_gen,
        patch("src.clinical_notes.llm._get_anthropic_client"),
    ):
        mock_gen.return_value = "response text"
        from src.clinical_notes.llm import generate

        result = await generate("sys", "user", model="anthropic/claude-sonnet-4-20250514")
        assert result == "response text"
        mock_gen.assert_called_once()
        args = mock_gen.call_args
        assert args[0][1] == "claude-sonnet-4-20250514"


@pytest.mark.asyncio
async def test_generate_dispatches_to_openai():
    with (
        patch("src.clinical_notes.llm._openai.generate", new_callable=AsyncMock) as mock_gen,
        patch("src.clinical_notes.llm._get_openai_client"),
    ):
        mock_gen.return_value = "openai response"
        from src.clinical_notes.llm import generate

        result = await generate("sys", "user", model="openai/gpt-4o")
        assert result == "openai response"
        mock_gen.assert_called_once()
        args = mock_gen.call_args
        assert args[0][1] == "gpt-4o"


@pytest.mark.asyncio
async def test_generate_structured_dispatches_to_anthropic():
    with (
        patch(
            "src.clinical_notes.llm._anthropic.generate_structured", new_callable=AsyncMock
        ) as mock_gen,
        patch("src.clinical_notes.llm._get_anthropic_client"),
    ):
        mock_gen.return_value = SampleModel(name="test", value=42)
        from src.clinical_notes.llm import generate_structured

        result = await generate_structured(
            "sys", "user", SampleModel, model="anthropic/claude-sonnet-4-20250514"
        )
        assert result.name == "test"
        assert result.value == 42


@pytest.mark.asyncio
async def test_generate_structured_dispatches_to_openai():
    with (
        patch(
            "src.clinical_notes.llm._openai.generate_structured", new_callable=AsyncMock
        ) as mock_gen,
        patch("src.clinical_notes.llm._get_openai_client"),
    ):
        mock_gen.return_value = SampleModel(name="test", value=1)
        from src.clinical_notes.llm import generate_structured

        result = await generate_structured("sys", "user", SampleModel, model="openai/gpt-4o")
        assert result.name == "test"
        mock_gen.assert_called_once()
        # Should pass supports_json_schema=True for OpenAI
        kwargs = mock_gen.call_args[1]
        assert kwargs["supports_json_schema"] is True


@pytest.mark.asyncio
async def test_generate_structured_ollama_no_json_schema():
    with (
        patch(
            "src.clinical_notes.llm._openai.generate_structured", new_callable=AsyncMock
        ) as mock_gen,
        patch("src.clinical_notes.llm._get_openai_client"),
    ):
        mock_gen.return_value = SampleModel(name="test", value=1)
        from src.clinical_notes.llm import generate_structured

        await generate_structured("sys", "user", SampleModel, model="ollama/llama3")
        # Should pass supports_json_schema=False for Ollama
        kwargs = mock_gen.call_args[1]
        assert kwargs["supports_json_schema"] is False


# --- Provider-level tests ---


@pytest.mark.asyncio
async def test_anthropic_generate():
    from src.clinical_notes.llm import _anthropic

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="hello")]
    mock_client.messages.create.return_value = mock_response

    result = await _anthropic.generate(mock_client, "claude-sonnet-4-20250514", "sys", "user", 3)
    assert result == "hello"
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_anthropic_structured_tool_use():
    from src.clinical_notes.llm import _anthropic

    mock_client = AsyncMock()
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {"name": "test", "value": 42}
    mock_response = MagicMock()
    mock_response.content = [tool_block]
    mock_client.messages.create.return_value = mock_response

    result = await _anthropic.generate_structured(
        mock_client, "claude-sonnet-4-20250514", "sys", "user", SampleModel, 3
    )
    assert isinstance(result, SampleModel)
    assert result.name == "test"
    assert result.value == 42

    # Verify tool_choice was set correctly
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["tool_choice"]["type"] == "tool"
    assert "extract_SampleModel" in call_kwargs["tool_choice"]["name"]


@pytest.mark.asyncio
async def test_openai_generate():
    from src.clinical_notes.llm import _openai

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "hello from openai"
    mock_client.chat.completions.create.return_value = mock_response

    result = await _openai.generate(mock_client, "gpt-4o", "sys", "user", 3)
    assert result == "hello from openai"


@pytest.mark.asyncio
async def test_openai_structured_json_schema():
    from src.clinical_notes.llm import _openai

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"name": "test", "value": 42}'
    mock_client.chat.completions.create.return_value = mock_response

    result = await _openai.generate_structured(
        mock_client, "gpt-4o", "sys", "user", SampleModel, 3, supports_json_schema=True
    )
    assert isinstance(result, SampleModel)
    assert result.name == "test"

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["response_format"]["type"] == "json_schema"
    assert call_kwargs["response_format"]["json_schema"]["name"] == "SampleModel"


@pytest.mark.asyncio
async def test_openai_structured_ollama_fallback():
    from src.clinical_notes.llm import _openai

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"name": "test", "value": 42}'
    mock_client.chat.completions.create.return_value = mock_response

    result = await _openai.generate_structured(
        mock_client, "llama3", "sys", "user", SampleModel, 3, supports_json_schema=False
    )
    assert isinstance(result, SampleModel)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["response_format"] == {"type": "json_object"}
    # Schema should be injected into system prompt
    sys_msg = call_kwargs["messages"][0]["content"]
    assert "JSON" in sys_msg
    assert "SampleModel" not in call_kwargs.get("response_format", {}).get("json_schema", {})


@pytest.mark.asyncio
async def test_retry_on_failure():
    from src.clinical_notes.llm import _openai

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "success"
    mock_client.chat.completions.create.side_effect = [
        RuntimeError("fail"),
        mock_response,
    ]

    result = await _openai.generate(mock_client, "gpt-4o", "sys", "user", 3)
    assert result == "success"
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted():
    from src.clinical_notes.llm import _openai

    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError, match="fail"):
        await _openai.generate(mock_client, "gpt-4o", "sys", "user", 2)
    assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_anthropic_retry_on_failure():
    from src.clinical_notes.llm import _anthropic

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="success")]
    mock_client.messages.create.side_effect = [
        RuntimeError("fail"),
        mock_response,
    ]

    result = await _anthropic.generate(mock_client, "claude-sonnet-4-20250514", "sys", "user", 3)
    assert result == "success"
    assert mock_client.messages.create.call_count == 2
