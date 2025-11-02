"""Tool 1 of 3: calculator."""

import ast
import operator
import time

from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2] / "workspace"

FAKE_LATENCY_S = 0.8   # pretend get_weather and search_web hit a real API

class ToolError(Exception):
    """A failure the model should read as text and recover from."""


# --- the menu the model sees ---
CALCULATOR_SCHEMA = {
    "name": "calculator",
    "description": (
        "Evaluate an arithmetic expression and return the result. "
        "Supports + - * / ** and parentheses. Numbers only, no variables. "
        'Example: calculator(expression="(2400 * 18.5) / 100")'
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Arithmetic expression, e.g. '(2400 * 18.5) / 100'",
            }
        },
        "required": ["expression"],
    },
}


# --- the kitchen that actually runs ---
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _walk(node):
    """Allow numbers and math. Reject everything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _walk(node.left), _walk(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ToolError("exponent too large, keep it under 100")
        if isinstance(node.op, ast.Div) and right == 0:
            raise ToolError("division by zero")
        return _OPS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_walk(node.operand)

    raise ToolError(f"only plain arithmetic is allowed, got: {expression_hint(node)}")


def expression_hint(node) -> str:
    return type(node).__name__


def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ToolError(f"could not parse {expression!r}: {e.msg}") from e
    return str(_walk(tree.body))


# --- tool 2 of 3: weather ---

GET_WEATHER_SCHEMA = {
    "name": "get_weather",
    "description": (
        "Get the current weather for a city. "
        'Example: get_weather(city="Paris", unit="celsius")'
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit. Defaults to celsius.",
            },
        },
        "required": ["city"],
    },
}

_FAKE_WEATHER = {
    "paris": (14.0, "overcast"),
    "san francisco": (17.0, "foggy"),
    "new york": (9.0, "clear"),
    "bengaluru": (27.0, "humid, light rain"),
}


def get_weather(city: str, unit: str = "celsius") -> str:
    time.sleep(FAKE_LATENCY_S)
    key = city.split(",")[0].strip().lower()
    if key not in _FAKE_WEATHER:
        raise ToolError(
            f"no weather data for {city!r}. Known cities: "
            + ", ".join(sorted(_FAKE_WEATHER))
        )
    celsius, conditions = _FAKE_WEATHER[key]
    if unit == "fahrenheit":
        return f"{celsius * 9 / 5 + 32:.1f}°F, {conditions}"
    return f"{celsius:.1f}°C, {conditions}"


# --- tool 3 of 3: search ---

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


def search_web(query: str, limit: int = 3) -> str:
    time.sleep(FAKE_LATENCY_S)
    return "\n".join(
        f"{i}. Result {i} for {query!r} - https://example.com/{i}"
        for i in range(1, limit + 1)
    )


# --- tool 4 and 5: files, locked to one folder ---

def _safe_path(name: str) -> Path:
    """Turn a filename into a real path, or refuse if it escapes the folder."""
    WORKSPACE.mkdir(exist_ok=True)
    target = (WORKSPACE / name).resolve()
    if not target.is_relative_to(WORKSPACE.resolve()):
        raise ToolError(f"{name!r} is outside the workspace folder. Not allowed.")
    return target


LIST_FILES_SCHEMA = {
    "name": "list_files",
    "description": "List the files available in the workspace folder. Takes no arguments.",
    "input_schema": {"type": "object", "properties": {}},
}


def list_files() -> str:
    WORKSPACE.mkdir(exist_ok=True)
    names = sorted(p.name for p in WORKSPACE.iterdir() if p.is_file())
    return "\n".join(names) if names else "(the workspace folder is empty)"


READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": (
        "Read a text file from the workspace folder. "
        'Example: read_file(name="notes.txt")'
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Filename, e.g. 'notes.txt'"}
        },
        "required": ["name"],
    },
}


def read_file(name: str) -> str:
    path = _safe_path(name)
    if not path.is_file():
        raise ToolError(f"no file named {name!r}. Use list_files to see what exists.")
    text = path.read_text(errors="replace")
    if len(text) > 4000:
        return text[:4000] + f"\n[... cut off, the file is {len(text)} characters]"
    return text


WRITE_FILE_SCHEMA = {
    "name": "write_file",
    "description": (
        "Write text to a file in the workspace folder. Overwrites if it exists. "
        'Example: write_file(name="summary.txt", content="hello")'
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Filename, e.g. 'summary.txt'"},
            "content": {"type": "string", "description": "The text to write"},
        },
        "required": ["name", "content"],
    },
}


def write_file(name: str, content: str) -> str:
    path = _safe_path(name)
    existed = path.is_file()
    path.write_text(content)
    return f"{'overwrote' if existed else 'created'} {name} ({len(content)} characters)"


# --- the menu, and one door into all three ---
TOOL_SCHEMAS = [CALCULATOR_SCHEMA, GET_WEATHER_SCHEMA, SEARCH_WEB_SCHEMA,
                LIST_FILES_SCHEMA, READ_FILE_SCHEMA, WRITE_FILE_SCHEMA]

_FUNCTIONS = {"calculator": calculator, "get_weather": get_weather,
              "search_web": search_web, "list_files": list_files,
              "read_file": read_file, "write_file": write_file}

RISKY_TOOLS = {"write_file"}


def run_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run any tool by name. Returns (text_for_the_model, is_error)."""
    fn = _FUNCTIONS.get(name)
    if fn is None:
        return (
            f"Error: no tool named {name!r}. Available: "
            + ", ".join(sorted(_FUNCTIONS)),
            True,
        )
    try:
        return fn(**tool_input), False
    except ToolError as e:
        return f"Error: {e}", True
    except TypeError as e:
        return f"Error: bad arguments for {name}: {e}", True