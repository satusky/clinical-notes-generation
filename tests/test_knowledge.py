from unittest.mock import AsyncMock, patch

import pytest

from src.clinical_notes.knowledge import KnowledgeLoader, _strip_html
from src.clinical_notes.models.investigation import KnowledgeSource, KnowledgeSourceType


class TestStripHtml:
    def test_basic(self):
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_plain_text(self):
        assert _strip_html("no tags here") == "no tags here"


class TestLoadFile:
    def test_reads_file(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("clinical data here")
        loader = KnowledgeLoader()
        assert loader._load_file(str(f)) == "clinical data here"


class TestLoadDirectory:
    def test_reads_multiple_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("file a")
        (tmp_path / "b.md").write_text("file b")
        (tmp_path / "c.json").write_text('{"key": "value"}')
        (tmp_path / "d.py").write_text("ignored")

        loader = KnowledgeLoader()
        result = loader._load_directory(str(tmp_path))
        assert "file a" in result
        assert "file b" in result
        assert '"key"' in result
        assert "ignored" not in result


class TestTruncation:
    @pytest.mark.asyncio
    async def test_truncates_to_max_chars(self, tmp_path):
        f = tmp_path / "long.txt"
        f.write_text("x" * 500)
        loader = KnowledgeLoader(max_chars=100)
        source = KnowledgeSource(
            source_type=KnowledgeSourceType.LOCAL_FILE, location=str(f)
        )
        result = await loader.load(source)
        assert len(result) == 100


class TestFetchUrl:
    @pytest.mark.asyncio
    async def test_fetches_and_strips_html(self):
        loader = KnowledgeLoader()
        mock_response = AsyncMock()
        mock_response.text = "<html><body><p>Study results</p></body></html>"
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("src.clinical_notes.knowledge.httpx.AsyncClient", return_value=mock_client):
            source = KnowledgeSource(
                source_type=KnowledgeSourceType.WEB_URL,
                location="https://example.com/study",
            )
            result = await loader.load(source)
        assert "Study results" in result
