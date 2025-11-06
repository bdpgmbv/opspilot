from pathlib import Path

from pydantic import BaseModel, ValidationError

WORKSPACE = Path(__file__).resolve().parents[3] / "workspace"

FAKE_LATENCY_S = 0.8   # pretend get_weather and search_web hit a real API

REGISTRY: dict[str, dict] = {}


class ToolError(Exception):
    """A failure the model should read as text and recover from."""


def _anthropic_schema(name: str, description: str, model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)
    return {"name": name, "description": description, "input_schema": schema}


def tool(name: str, description: str, model: type[BaseModel], risky: bool = False):
    """Register a function as a tool. The model is both the schema and the rule."""
    schema = _anthropic_schema(name, description, model)

    def decorator(fn):
        REGISTRY[name] = {"schema": schema, "fn": fn, "model": model, "risky": risky}
        return fn

    return decorator


def validate(name: str, tool_input: dict) -> dict:
    return REGISTRY[name]["model"](**tool_input).model_dump()


def validation_error_text(name: str, e: ValidationError) -> str:
    parts = [
        f"{'.'.join(str(p) for p in err['loc']) or 'input'}: {err['msg']}"
        for err in e.errors()
    ]
    return f"Error: bad arguments for {name}. " + "; ".join(parts)


def safe_path(name: str) -> Path:
    """Turn a filename into a real path, or refuse if it escapes the folder."""
    WORKSPACE.mkdir(exist_ok=True)
    target = (WORKSPACE / name).resolve()
    if not target.is_relative_to(WORKSPACE.resolve()):
        raise ToolError(f"{name!r} is outside the workspace folder. Not allowed.")
    return target