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

    # API keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Local model endpoints
    ollama_base_url: str = "http://localhost:11434/v1"
    vllm_base_url: str = "http://localhost:8000/v1"

    output_dir: str = "output"
    log_level: str = "INFO"
    max_retries: int = 3

    def model_for(self, agent_name: str) -> str:
        override = getattr(self, f"{agent_name}_model", None)
        return override or self.default_model


settings = Settings()
