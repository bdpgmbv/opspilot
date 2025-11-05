from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError as MCPToolError
from pydantic import Field

from opspilot.tools.base import ToolError
from opspilot.tools.files import READ_FILE_SCHEMA
from opspilot.tools.files import read_file as _read_file
from opspilot.tools.sql import SQL_QUERY_SCHEMA
from opspilot.tools.sql import sql_query as _sql_query

mcp = MCPServer(name="opspilot-data", version="0.1.0")


def _param(schema: dict, name: str) -> str:
    return schema["input_schema"]["properties"][name]["description"]


@mcp.tool(description=SQL_QUERY_SCHEMA["description"])
def sql_query(sql: Annotated[str, Field(description=_param(SQL_QUERY_SCHEMA, "sql"))]) -> str:
    try:
        return _sql_query(sql)
    except ToolError as e:
        raise MCPToolError(str(e)) from e  # keeps our message; anything else is a crash


@mcp.tool(description=READ_FILE_SCHEMA["description"])
def read_file(name: Annotated[str, Field(description=_param(READ_FILE_SCHEMA, "name"))]) -> str:
    try:
        return _read_file(name)
    except ToolError as e:
        raise MCPToolError(str(e)) from e


if __name__ == "__main__":
    mcp.run()  # stdio
