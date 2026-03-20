"""Knowledge source loader for investigator agents."""

import logging
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

import httpx

from .config import settings
from .models.investigation import KnowledgeSource, KnowledgeSourceType

logger = logging.getLogger(__name__)


class _HTMLTextExtractor(HTMLParser):
    """Simple HTML-to-text converter."""

    def __init__(self):
        super().__init__()
        self._result = StringIO()

    def handle_data(self, data: str):
        self._result.write(data)

    def get_text(self) -> str:
        return self._result.getvalue()


def _strip_html(html: str) -> str:
    extractor = _HTMLTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


class KnowledgeLoader:
    """Loads content from knowledge sources for use in investigator prompts."""

    def __init__(self, max_chars: int | None = None):
        self.max_chars = max_chars or settings.knowledge_source_max_chars

    async def load(self, source: KnowledgeSource) -> str:
        """Load content from a knowledge source, truncated to max_chars."""
        if source.source_type == KnowledgeSourceType.LOCAL_FILE:
            content = self._load_file(source.location)
        elif source.source_type == KnowledgeSourceType.LOCAL_DIRECTORY:
            content = self._load_directory(source.location)
        elif source.source_type == KnowledgeSourceType.WEB_URL:
            content = await self._fetch_url(source.location)
        else:
            logger.warning("Unknown source type: %s", source.source_type)
            return ""

        if len(content) > self.max_chars:
            logger.info(
                "Truncating content from %d to %d chars", len(content), self.max_chars
            )
            content = content[: self.max_chars]
        return content

    def _load_file(self, path: str) -> str:
        text = Path(path).read_text(encoding="utf-8")
        logger.debug("Loaded file: %s (%d chars)", path, len(text))
        return text

    def _load_directory(self, path: str) -> str:
        parts = []
        dir_path = Path(path)
        for ext in ("*.txt", "*.md", "*.json"):
            for file in sorted(dir_path.glob(ext)):
                parts.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}")
        logger.debug("Loaded directory: %s (%d files)", path, len(parts))
        return "\n\n".join(parts)

    async def _fetch_url(self, url: str) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()
            text = _strip_html(response.text)
            logger.debug("Fetched URL: %s (%d chars)", url, len(text))
            return text
