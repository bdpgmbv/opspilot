# OpsPilot

An AI agent that takes a goal, works it out with real tools, and asks
permission before it changes anything.

Built without an agent framework, on purpose. The loop is 60 lines of
plain Python, so there is nothing hidden.

## What it can do today

- Plans and runs multi-step work: query a database, read a file, do the maths, write a result.
- Runs independent tool calls at the same time.
- Stops on a step limit or a cost budget, whichever comes first.
- Asks a human before any write. Nothing irreversible happens unapproved.
- Records every run and every tool call in Postgres, with a full trace in Langfuse.

Example:

```
$ uv run python -m opspilot.agent "Why did signups drop yesterday?"

--- step 1 --- tool_use   sql_query(...)   count by day
--- step 2 --- tool_use   sql_query(...)   split by source, country, plan
--- step 3 --- end_turn

ANSWER: Signups fell to 29 from the usual 40 because ad-sourced
signups dropped to zero. Organic and referral were normal.
```

## Stack

| Piece | Choice |
|---|---|
| Model | Claude (Anthropic), with an OpenAI comparison script |
| Agent loop | plain Python, no framework |
| Tool contracts | Pydantic models, strict validation |
| Tool sharing | MCP server over stdio |
| Store | Postgres 17 + pgvector, in Docker |
| Tracing | Langfuse + OpenTelemetry |
| Tests | pytest |

## Tools

| Tool | Notes |
|---|---|
| `calculator` | AST evaluator, never `eval()` |
| `sql_query` | read-only Postgres role, 5s timeout, 50-row cap |
| `read_file` / `write_file` / `list_files` | locked to `workspace/`, no path escapes |
| `get_weather` / `search_web` | stubs, pending real APIs |

Every tool declares its arguments as a Pydantic model. That one model is both
the schema the model reads and the rule the input is checked against, so the
two cannot drift apart. Bad arguments come back as a sentence naming the field.

`sql_query` and `read_file` are also exposed over MCP, so other clients can
use them. See `mcp_server/`.

## Running it

Needs Docker and an Anthropic API key.

```bash
cp .env.example .env     # then fill in your keys
uv sync
docker compose up -d
docker compose exec -T postgres psql -U opspilot -d opspilot < seed.sql
uv run python -m opspilot.agent "Why did signups drop yesterday?"
```

Tests (no API key needed, but Docker must be up):

```bash
uv run pytest -q
```

Benchmark:

```bash
uv run python -m benchmark.run
```

## Layout

```
src/opspilot/
├── agent.py        the loop
├── config.py       every setting, read from .env
├── db.py           Postgres writes
├── mcp_client.py   talks to the MCP server when USE_MCP=1
└── tools/          one file per tool, assembled by a decorator registry
mcp_server/         two tools exposed over MCP, for other clients
benchmark/          tasks with checkable end states
tests/              pytest
scripts/            mcp_probe.py, for checking the MCP server by hand
learning/           the step-by-step exercises this was built from
```

Adding a tool is one new file in `tools/` plus one import line. The schema
list, the risky-tool set and the input validation all build themselves from
the Pydantic model.

## Where this is going

Built to the OpsPilot brief, six levels. Levels 0 and 1 are done.

| Level | State |
|---|---|
| 0 — tool calling by hand, two providers | done |
| 1 — the loop, real tools, tracing | MCP and validation done; web search, Python sandbox and 30 tasks pending |
| 2 — LangGraph state machine, memory, multi-agent | next |
| 3 — evaluation and safety | |
| 4 — durable execution with Temporal | |
| 5 — production hardening | |

Target at Level 5: 70% success on 150 tasks, median under 12 tool calls,
under $0.40 a task, crash-resume with no duplicated side effects.
