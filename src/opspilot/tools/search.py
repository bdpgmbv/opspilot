import time

from opspilot.tools import base
from opspilot.tools.base import tool

SEARCH_WEB_SCHEMA = {
    "name": "search_web",
    "description": (
        "Search the web and return result titles with URLs. "
        'Example: search_web(query="SQLite WAL mode", limit=3)'
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for"},
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "description": "How many results. Defaults to 3.",
            },
        },
        "required": ["query"],
    },
}


@tool(SEARCH_WEB_SCHEMA)
def search_web(query: str, limit: int = 3) -> str:
    time.sleep(base.FAKE_LATENCY_S)   # read at call time, so tests can turn it off
    return "\n".join(
        f"{i}. Result {i} for {query!r} - https://example.com/{i}"
        for i in range(1, limit + 1)
    )
