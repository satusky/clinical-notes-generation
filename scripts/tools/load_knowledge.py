"""Load knowledge source content. Reads JSON array of KnowledgeSource objects from stdin.

Stdin format: [{"source_type": "local_file", "location": "/path/to/file"}, ...]
Optional: include "indices" key at top level to filter: {"sources": [...], "indices": [0, 2]}

Outputs: JSON object mapping index to loaded content.
"""

import asyncio
import json
import sys

from src.clinical_notes.knowledge import KnowledgeLoader
from src.clinical_notes.models.investigation import KnowledgeSource


async def load_sources(sources: list[KnowledgeSource], indices: list[int] | None) -> dict:
    loader = KnowledgeLoader()
    results = {}

    targets = indices if indices is not None else list(range(len(sources)))
    for idx in targets:
        if 0 <= idx < len(sources):
            try:
                content = await loader.load(sources[idx])
                results[str(idx)] = {
                    "location": sources[idx].location,
                    "content": content,
                }
            except Exception as e:
                results[str(idx)] = {
                    "location": sources[idx].location,
                    "error": str(e),
                }
    return results


def main():
    raw = sys.stdin.read().strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    indices = None
    if isinstance(data, dict):
        sources_data = data.get("sources", [])
        indices = data.get("indices")
    else:
        sources_data = data

    sources = [KnowledgeSource.model_validate(s) for s in sources_data]
    results = asyncio.run(load_sources(sources, indices))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
