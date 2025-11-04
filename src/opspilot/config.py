import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _float(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


def _bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes"}


# --- models -----------------------------------------------------------

MODEL = os.environ.get("MODEL", "claude-opus-5-5")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")

# $ per million tokens: (input, output)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def price(model: str) -> tuple[float, float]:
    """Price per million tokens. Fails loudly rather than logging a wrong cost."""
    if model not in PRICES:
        raise RuntimeError(
            f"no price listed for {model!r}. Add it to PRICES in config.py, "
            "or the cost log will be wrong."
        )
    return PRICES[model]


# --- agent limits -----------------------------------------------------

MAX_STEPS = _int("MAX_STEPS", 10)
MAX_COST_USD = _float("MAX_COST_USD", 0.25)
MAX_TOKENS = _int("MAX_TOKENS", 1024)
PARALLEL = _bool("PARALLEL", True)
REQUIRE_APPROVAL = _bool("REQUIRE_APPROVAL", True)
LOG_PREVIEW_CHARS = _int("LOG_PREVIEW_CHARS", 200)


# --- secrets ----------------------------------------------------------


def anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY missing. Copy .env.example to .env and fill it in."
        )
    return key


def openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing. Add it to .env.")
    return key


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL missing. Add it to .env.")
    return url


def database_url_ro() -> str:
    url = os.environ.get("DATABASE_URL_RO")
    if not url:
        raise RuntimeError("DATABASE_URL_RO missing. Add it to .env.")
    return url
