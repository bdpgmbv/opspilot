from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError as MCPToolError

from opspilot.tools.base import ToolError
from opspilot.tools.files import READ_DESCRIPTION, ReadFileInput
from opspilot.tools.files import read_file as _read_file
from opspilot.tools.sql import DESCRIPTION as SQL_DESCRIPTION
from opspilot.tools.sql import SqlQueryInput
from opspilot.tools.sql import sql_query as _sql_query

mcp = MCPServer(name="opspilot-data", version="0.1.0")

Sql = Annotated[str, SqlQueryInput.model_fields["sql"]]
FileName = Annotated[str, ReadFileInput.model_fields["name"]]


@mcp.tool(description=SQL_DESCRIPTION)
def sql_query(sql: Sql) -> str:
    try:
        return _sql_query(sql)
    except ToolError as e:
        raise MCPToolError(str(e)) from e


@mcp.tool(description=READ_DESCRIPTION)
def read_file(name: FileName) -> str:
    try:
        return _read_file(name)
    except ToolError as e:
        raise MCPToolError(str(e)) from e


if __name__ == "__main__":
    mcp.run()  # stdio