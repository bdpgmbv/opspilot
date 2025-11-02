"""Loads .env once. Everything else imports from here."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Walk up from this file to the project root, load the .env sitting there
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = "claude-opus-5-5"


def anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY missing. Copy .env.example to .env and fill it in."
        )
    return key


OPENAI_MODEL = "gpt-5.6-luna"   # verify against your own account, see below


def openai_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing. Add it to .env.")
    return key


# claude-opus-5-5, $ per million tokens
PRICE_IN = 4.00
PRICE_OUT = 20.00