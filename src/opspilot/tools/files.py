from pydantic import BaseModel, ConfigDict, Field

from opspilot.tools.base import WORKSPACE, ToolError, safe_path, tool

MAX_READ_CHARS = 4000

LIST_DESCRIPTION = "List the files available in the workspace folder. Takes no arguments."


class ListFilesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


@tool("list_files", LIST_DESCRIPTION, ListFilesInput)
def list_files() -> str:
    WORKSPACE.mkdir(exist_ok=True)
    names = sorted(p.name for p in WORKSPACE.iterdir() if p.is_file())
    return "\n".join(names) if names else "(the workspace folder is empty)"


READ_DESCRIPTION = (
    "Read a text file from the workspace folder. "
    'Example: read_file(name="notes.txt")'
)


class ReadFileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1, max_length=120, description="Filename, e.g. 'notes.txt'"
    )


@tool("read_file", READ_DESCRIPTION, ReadFileInput)
def read_file(name: str) -> str:
    path = safe_path(name)
    if not path.is_file():
        raise ToolError(f"no file named {name!r}. Use list_files to see what exists.")
    text = path.read_text(errors="replace")
    if len(text) > MAX_READ_CHARS:
        return text[:MAX_READ_CHARS] + f"\n[... cut off, the file is {len(text)} characters]"
    return text


WRITE_DESCRIPTION = (
    "Write text to a file in the workspace folder. Overwrites if it exists. "
    'Example: write_file(name="summary.txt", content="hello")'
)


class WriteFileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1, max_length=120, description="Filename, e.g. 'summary.txt'"
    )
    content: str = Field(max_length=100_000, description="The text to write")


@tool("write_file", WRITE_DESCRIPTION, WriteFileInput, risky=True)
def write_file(name: str, content: str) -> str:
    path = safe_path(name)
    existed = path.is_file()
    path.write_text(content)
    return f"{'overwrote' if existed else 'created'} {name} ({len(content)} characters)"