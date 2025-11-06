import psycopg
from pydantic import BaseModel, ConfigDict, Field

from opspilot.config import database_url_ro
from opspilot.tools.base import ToolError, tool

DESCRIPTION = (
    "Run a read-only SQL SELECT on the analytics database. "
    "Table: demo.signups(signup_date date, plan text, country text, source text). "
    "Returns up to 50 rows as text. "
    'Example: sql_query(sql="SELECT signup_date, count(*) FROM demo.signups '
    'GROUP BY 1 ORDER BY 1 DESC LIMIT 7")'
)


class SqlQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sql: str = Field(
        min_length=1, max_length=4000, description="A single SELECT statement"
    )


MAX_ROWS = 50
STATEMENT_TIMEOUT_MS = 5000


@tool("sql_query", DESCRIPTION, SqlQueryInput)
def sql_query(sql: str) -> str:
    url = database_url_ro()

    try:
        with psycopg.connect(
            url, options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}"
        ) as conn:
            conn.read_only = True
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description is None:
                    raise ToolError("that statement returned no rows to read.")
                cols = [c.name for c in cur.description]
                rows = cur.fetchmany(MAX_ROWS + 1)
    except psycopg.Error as e:
        detail = (e.diag.message_primary or str(e)).strip()
        hint = (e.diag.message_hint or "").strip()
        raise ToolError(f"{detail}{'. ' + hint if hint else ''}") from e

    if not rows:
        return "(0 rows)"
    out = [" | ".join(cols)]
    out += [" | ".join("" if v is None else str(v) for v in r) for r in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        out.append(f"[... cut off at {MAX_ROWS} rows]")
    return "\n".join(out)