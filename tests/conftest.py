import psycopg
import pytest

from opspilot.config import database_url_ro
from opspilot.tools import base

base.FAKE_LATENCY_S = 0.0


def _postgres_is_up() -> bool:
    try:
        with psycopg.connect(database_url_ro(), connect_timeout=2):
            return True
    except Exception:
        return False


needs_postgres = pytest.mark.skipif(
    not _postgres_is_up(),
    reason="Postgres is not reachable. Run: docker compose up -d",
)
