import asyncio
import sys

from mcp import Client, StdioServerParameters

PARAMS = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"])


async def main() -> None:
    async with Client(PARAMS) as client:
        listing = await client.list_tools()
        for t in listing.tools:
            print(f"tool: {t.name}")
            print(f"  description: {t.description[:70]}...")
            print(f"  input_schema: {t.input_schema}")

        result = await client.call_tool("sql_query", {"sql": "SELECT count(*) FROM demo.signups"})
        print(f"\nsql_query -> {result.content[0].text}")

        bad = await client.call_tool("read_file", {"name": "../.env"})
        print(f"read_file('../.env') -> isError={bad.is_error} {bad.content[0].text[:60]}")


if __name__ == "__main__":
    asyncio.run(main())
