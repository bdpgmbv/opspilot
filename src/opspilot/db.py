"""Postgres writes. Replaces costs.csv."""

import json
import os

import psycopg

from opspilot.config import MODEL


def _conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL missing. Add it to .env.")
    return psycopg.connect(url)


def start_run(run_id: str, question: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO runs (run_id, model, question) VALUES (%s, %s, %s)",
            (run_id, MODEL, question),
        )


def save_event(run_id, step, tool, tool_input, output, is_error, approval) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT INTO audit_events
               (run_id, step, tool, tool_input, output, is_error, approval)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (run_id, step, tool, json.dumps(tool_input),
             output[:2000], is_error, approval),
        )


def finish_run(run) -> None:
    with _conn() as conn:
        conn.execute(
            """UPDATE runs SET steps=%s, tokens_in=%s, tokens_out=%s,
                               cost_usd=%s, seconds=%s, stopped_because=%s,
                               finished_at=now()
               WHERE run_id=%s""",
            (run.steps, run.tokens_in, run.tokens_out, run.cost_usd,
             run.seconds, run.stopped_because, run.run_id),
        )