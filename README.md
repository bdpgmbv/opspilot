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
└── tools/          one file per tool, assembled by a decorator registry
benchmark/          tasks with checkable end states
scripts/            the step-by-step exercises this was built from
docs/adr/           decisions and why
```

Adding a tool is one new file in `tools/` plus one import line. The schema
list and the risky-tool set build themselves.

## Where this is going

Built to the OpsPilot brief, six levels. Levels 0 and 1 are done.

| Level | State |
|---|---|
| 0 — tool calling by hand, two providers | done |
| 1 — the loop, real tools, tracing | done, MCP server pending |
| 2 — LangGraph state machine, memory, multi-agent | next |
| 3 — evaluation and safety | |
| 4 — durable execution with Temporal | |
| 5 — production hardening | |

Target at Level 5: 70% success on 150 tasks, median under 12 tool calls,
under $0.40 a task, crash-resume with no duplicated side effects.

See `JOURNAL.md` for what broke along the way.
