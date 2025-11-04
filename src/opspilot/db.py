import json

import psycopg

from opspilot.config import MODEL, database_url

_connection: psycopg.Connection | None = None


def _conn() -> psycopg.Connection:
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg.connect(database_url(), autocommit=True)
    return _connection


def start_run(run_id: str, question: str) -> None:
    """Insert the row empty, so audit events have something to point at."""
    _conn().execute(
        "INSERT INTO runs (run_id, model, question) VALUES (%s, %s, %s)",
        (run_id, MODEL, question),
    )


def save_event(run_id, step, tool, tool_input, output, is_error, approval) -> None:
    _conn().execute(
        """INSERT INTO audit_events
           (run_id, step, tool, tool_input, output, is_error, approval)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (run_id, step, tool, json.dumps(tool_input), output[:2000], is_error, approval),
    )


def finish_run(run) -> None:
    """Fill in the row. A row still NULL here means the run never finished."""
    _conn().execute(
        """UPDATE runs SET steps = %s, tokens_in = %s, tokens_out = %s,
                           cost_usd = %s, seconds = %s, stopped_because = %s,
                           finished_at = now()
           WHERE run_id = %s""",
        (run.steps, run.tokens_in, run.tokens_out, run.cost_usd,
         run.seconds, run.stopped_because, run.run_id),
    )
