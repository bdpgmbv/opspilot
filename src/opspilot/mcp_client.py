import asyncio
import sys
import threading

from mcp import Client, StdioServerParameters

MCP_TOOLS = {"sql_query", "read_file"}

PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])

_loop: asyncio.AbstractEventLoop | None = None
_client: Client | None = None


def _connect() -> None:
    global _loop, _client
    if _client is not None:
        return
    _loop = asyncio.new_event_loop()
    threading.Thread(target=_loop.run_forever, daemon=True).start()

    async def _open() -> Client:
        client = Client(PARAMS)
        await client.__aenter__()
        return client

    _client = asyncio.run_coroutine_threadsafe(_open(), _loop).result()


def call(name: str, args: dict) -> tuple[str, bool]:
    _connect()
    result = asyncio.run_coroutine_threadsafe(_client.call_tool(name, args), _loop).result()
    return result.content[0].text, result.is_error