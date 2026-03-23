"""High-level entry point for constructing a CaseConfig from a CaseSeed."""

import logging

from .agents.constructor import ConstructorAgent
from .models.case import CaseConfig
from .models.investigation import CaseSeed

logger = logging.getLogger(__name__)


class CaseBuilder:
    """Builds a CaseConfig from minimal seed input via the Constructor agent."""

    def __init__(self):
        self.constructor = ConstructorAgent()

    async def build_case(self, seed: CaseSeed) -> CaseConfig:
        logger.info(
            "Starting case build: %d raw variables, coding_system=%s",
            len(seed.raw_variables) if seed.raw_variables else 0,
            seed.coding_system,
        )
        config = await self.constructor.run(seed)
        logger.info("Case build complete: case_id=%s", config.case_id)
        return config
