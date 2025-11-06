import time

from pydantic import BaseModel, ConfigDict, Field

from opspilot.tools import base
from opspilot.tools.base import tool

DESCRIPTION = (
    "Search the web and return result titles with URLs. "
    'Example: search_web(query="SQLite WAL mode", limit=3)'
)


class SearchWebInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, description="What to search for")
    limit: int = Field(3, ge=1, le=10, description="How many results. Defaults to 3.")


@tool("search_web", DESCRIPTION, SearchWebInput)
def search_web(query: str, limit: int = 3) -> str:
    time.sleep(base.FAKE_LATENCY_S)   # read at call time, so tests can turn it off
    return "\n".join(
        f"{i}. Result {i} for {query!r} - https://example.com/{i}"
        for i in range(1, limit + 1)
    )