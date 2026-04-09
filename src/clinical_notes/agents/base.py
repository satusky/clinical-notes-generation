from abc import ABC, abstractmethod
import logging

from ..config import settings


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""

    agent_name: str = "base"
    prompt_version: str = "unknown"

    @property
    def model(self) -> str:
        return settings.model_for(self.agent_name)

    def maybe_log_prompts(self, logger: logging.Logger, system_prompt: str, user_prompt: str) -> None:
        if not settings.log_prompts:
            return
        logger.debug("[%s] System prompt:\n%s", self.agent_name, system_prompt)
        logger.debug("[%s] User prompt:\n%s", self.agent_name, user_prompt)

    @abstractmethod
    async def run(self, *args, **kwargs):
        ...
