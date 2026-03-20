from enum import Enum


class Provider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    VLLM = "vllm"


_PREFIX_MAP = {
    "openai": Provider.OPENAI,
    "anthropic": Provider.ANTHROPIC,
    "ollama": Provider.OLLAMA,
    "vllm": Provider.VLLM,
}


def parse_model(model_str: str) -> tuple[Provider, str]:
    """Parse 'provider/model_name' into (Provider, model_name).

    Raises ValueError for unknown prefixes.
    """
    if "/" not in model_str:
        raise ValueError(
            f"Model string must be in 'provider/model_name' format, got: {model_str}"
        )
    prefix, model_name = model_str.split("/", 1)
    provider = _PREFIX_MAP.get(prefix)
    if provider is None:
        raise ValueError(
            f"Unknown provider prefix '{prefix}'. "
            f"Supported: {', '.join(_PREFIX_MAP)}"
        )
    return provider, model_name
