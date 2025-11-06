from pydantic import ValidationError

from opspilot.config import USE_MCP
from opspilot.mcp_client import MCP_TOOLS
from opspilot.mcp_client import call as mcp_call
from opspilot.tools.arithmetic import calculator  # noqa: F401
from opspilot.tools.base import (  # noqa: F401
    REGISTRY,
    WORKSPACE,
    ToolError,
    safe_path,
    validate,
    validation_error_text,
)
from opspilot.tools.files import list_files, read_file, write_file  # noqa: F401
from opspilot.tools.search import search_web  # noqa: F401
from opspilot.tools.sql import sql_query  # noqa: F401
from opspilot.tools.weather import get_weather  # noqa: F401

TOOL_SCHEMAS = [entry["schema"] for entry in REGISTRY.values()]
RISKY_TOOLS = {name for name, entry in REGISTRY.items() if entry["risky"]}


def run_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run any tool by name. Returns (text_for_the_model, is_error)."""
    entry = REGISTRY.get(name)
    if entry is None:
        return (
            f"Error: no tool named {name!r}. Available: "
            + ", ".join(sorted(REGISTRY)),
            True,
        )
    if USE_MCP and name in MCP_TOOLS:
        return mcp_call(name, tool_input)
    try:
        tool_input = validate(name, tool_input)
    except ValidationError as e:
        return validation_error_text(name, e), True
    try:
        return entry["fn"](**tool_input), False
    except ToolError as e:
        return f"Error: {e}", True
    except TypeError as e:
        return f"Error: bad arguments for {name}: {e}", True