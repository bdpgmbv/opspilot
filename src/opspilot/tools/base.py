from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[3] / "workspace"

FAKE_LATENCY_S = 0.8   # pretend get_weather and search_web hit a real API

REGISTRY: dict[str, dict] = {}


class ToolError(Exception):
    """A failure the model should read as text and recover from."""


def tool(schema: dict, risky: bool = False):
    """Register a function as a tool. One decorator, one place to edit."""

    def decorator(fn):
        REGISTRY[schema["name"]] = {"schema": schema, "fn": fn, "risky": risky}
        return fn

    return decorator


def safe_path(name: str) -> Path:
    """Turn a filename into a real path, or refuse if it escapes the folder."""
    WORKSPACE.mkdir(exist_ok=True)
    target = (WORKSPACE / name).resolve()
    if not target.is_relative_to(WORKSPACE.resolve()):
        raise ToolError(f"{name!r} is outside the workspace folder. Not allowed.")
    return target
