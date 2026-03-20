from abc import ABC, abstractmethod

from ..config import settings


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""

    agent_name: str = "base"

    @property
    def model(self) -> str:
        return settings.model_for(self.agent_name)

    @abstractmethod
    async def run(self, *args, **kwargs):
        ...
