from opspilot.tools.base import WORKSPACE, ToolError, safe_path, tool

LIST_FILES_SCHEMA = {
    "name": "list_files",
    "description": "List the files available in the workspace folder. Takes no arguments.",
    "input_schema": {"type": "object", "properties": {}},
}


@tool(LIST_FILES_SCHEMA)
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


@tool(READ_FILE_SCHEMA)
def read_file(name: str) -> str:
    path = safe_path(name)
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


@tool(WRITE_FILE_SCHEMA, risky=True)
def write_file(name: str, content: str) -> str:
    path = safe_path(name)
    existed = path.is_file()
    path.write_text(content)
    return f"{'overwrote' if existed else 'created'} {name} ({len(content)} characters)"
