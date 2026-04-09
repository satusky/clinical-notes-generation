from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    default_model: str = "anthropic/claude-sonnet-4-20250514"

    # Per-agent model overrides
    narrator_model: str | None = None
    orchestrator_model: str | None = None
    coordinator_model: str | None = None
    clinician_model: str | None = None
    scribe_model: str | None = None
    constructor_model: str | None = None
    investigator_model: str | None = None

    # Knowledge source settings
    knowledge_source_max_chars: int = 10000

    # API keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    azure_openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_OPENAI_API_KEY", "AZURE_FOUNDRY_API_KEY"),
    )

    # OpenAI-compatible endpoints
    azure_openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_OPENAI_BASE_URL", "AZURE_FOUNDRY_BASE_URL"),
    )
    azure_openai_resource_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AZURE_OPENAI_RESOURCE_NAME", "AZURE_FOUNDRY_RESOURCE_NAME"),
    )
    azure_openai_supports_json_schema: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "AZURE_OPENAI_SUPPORTS_JSON_SCHEMA", "AZURE_FOUNDRY_SUPPORTS_JSON_SCHEMA"
        ),
    )

    # Local model endpoints
    ollama_base_url: str = "http://localhost:11434/v1"
    vllm_base_url: str = "http://localhost:8000/v1"

    output_dir: str = "output"
    log_level: str = "INFO"
    max_retries: int = 3
    validation_mode: Literal["warn", "strict"] = "warn"
    log_prompts: bool = False

    def model_for(self, agent_name: str) -> str:
        override = getattr(self, f"{agent_name}_model", None)
        return override or self.default_model


settings = Settings()
