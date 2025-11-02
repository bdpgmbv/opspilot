CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    model           TEXT NOT NULL,
    question        TEXT NOT NULL,
    steps           INT,
    tokens_in       INT,
    tokens_out      INT,
    cost_usd        NUMERIC(10,5),
    seconds         NUMERIC(8,1),
    stopped_because TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS audit_events (
    id         BIGSERIAL PRIMARY KEY,
    run_id     TEXT NOT NULL REFERENCES runs(run_id),
    step       INT NOT NULL,
    tool       TEXT NOT NULL,
    tool_input JSONB NOT NULL,
    output     TEXT,
    is_error   BOOLEAN NOT NULL,
    approval   TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);