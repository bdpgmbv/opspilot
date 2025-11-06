import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import anthropic
from langfuse import get_client, observe
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

from opspilot import db
from opspilot.config import (
    LOG_PREVIEW_CHARS,
    MAX_COST_USD,
    MAX_STEPS,
    MAX_TOKENS,
    MODEL,
    PARALLEL,
    REQUIRE_APPROVAL,
    anthropic_key,
    price,
)
from opspilot.tools import RISKY_TOOLS, TOOL_SCHEMAS, run_tool

AnthropicInstrumentor().instrument()  # must follow the config import, which loads .env

PRICE_IN, PRICE_OUT = price(MODEL)

# "Do not retry" stops the model re-asking until the step limit runs out.
DECLINED_MESSAGE = "Error: the human declined this action. Do not retry it."


@dataclass
class Run:
    run_id: str
    answer: str
    steps: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    seconds: float
    stopped_because: str  # answered | step_limit | cost_budget | refusal | crashed


def _ask_human(name: str, tool_input: dict) -> bool:
    print(f"\n  APPROVAL NEEDED -> {name}({tool_input})")
    return input("  allow? [y/N] ").strip().lower() == "y"


def _decide_approvals(calls, approve_all: bool) -> dict[str, str]:
    """Map tool_use_id to not_required | auto_granted | granted | declined."""
    decisions = {}
    for block in calls:
        if block.name not in RISKY_TOOLS:
            decisions[block.id] = "not_required"
        elif approve_all or not REQUIRE_APPROVAL:
            decisions[block.id] = "auto_granted"
        elif _ask_human(block.name, block.input):
            decisions[block.id] = "granted"
        else:
            decisions[block.id] = "declined"
    return decisions


@observe(name="tool", as_type="tool")
def _traced_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    text, is_error = run_tool(name, tool_input)
    get_client().update_current_span(
        name=f"tool:{name}",
        level="ERROR" if is_error else "DEFAULT",
    )
    return text, is_error


def _run_one(block, decisions: dict[str, str]) -> tuple[str, bool]:
    if decisions[block.id] == "declined":
        return DECLINED_MESSAGE, True
    return _traced_tool(block.name, block.input)


def _run_all(calls, decisions: dict[str, str]) -> list[tuple[str, bool]]:
    """Calls issued in one message cannot depend on each other, so they can overlap."""
    if PARALLEL and len(calls) > 1:
        with ThreadPoolExecutor(max_workers=8) as pool:
            return list(pool.map(lambda block: _run_one(block, decisions), calls))
    return [_run_one(block, decisions) for block in calls]


def _print_result(block, text: str, is_error: bool) -> None:
    mark = "ERR " if is_error else "    "
    cut = "... [cut off in log]" if len(text) > LOG_PREVIEW_CHARS else ""
    print(f"  {mark}{block.name}({block.input})")
    print(f"       -> {text[:LOG_PREVIEW_CHARS]}{cut}")


def _final_answer(response) -> tuple[str, str] | None:
    """Return (answer, stopped_because) when the model is finished, else None."""
    if response.stop_reason == "end_turn":
        return "".join(b.text for b in response.content if b.type == "text"), "answered"
    if response.stop_reason != "tool_use":  # refusal, max_tokens, pause_turn
        return f"[stopped: {response.stop_reason}]", response.stop_reason
    return None


def _handle_tool_calls(messages, response, run_id, step, approve_all, verbose) -> None:
    """Run the model's tool calls and append both messages the API requires."""
    messages.append({"role": "assistant", "content": response.content})  # verbatim

    calls = [b for b in response.content if b.type == "tool_use"]
    decisions = _decide_approvals(calls, approve_all)  # ask before any thread starts
    outputs = _run_all(calls, decisions)

    results = []
    for block, (text, is_error) in zip(calls, outputs, strict=True):
        if verbose:
            _print_result(block, text, is_error)
        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,  # must match the tool_use
            "content": text,
            "is_error": is_error,
        })
        db.save_event(run_id, step, block.name, block.input,
                      text, is_error, decisions[block.id])

    messages.append({"role": "user", "content": results})  # all results, one message


@observe(name="agent_run", as_type="agent")
def run_agent(question: str, verbose: bool = True, approve_all: bool = False) -> Run:
    client = anthropic.Anthropic(api_key=anthropic_key())
    messages = [{"role": "user", "content": question}]

    run_id = uuid.uuid4().hex[:8]
    db.start_run(run_id, question)  # insert empty; audit events reference it

    started = time.monotonic()
    tok_in = tok_out = 0
    step = 0
    answer = f"[gave up after {MAX_STEPS} steps]"
    stopped = "step_limit"

    def spent() -> float:
        return tok_in / 1e6 * PRICE_IN + tok_out / 1e6 * PRICE_OUT

    try:
        for step in range(1, MAX_STEPS + 1):
            if spent() >= MAX_COST_USD:  # before the call, or we always overshoot by one
                stopped = "cost_budget"
                answer = f"[stopped: spent ${spent():.4f} of ${MAX_COST_USD} budget]"
                break

            response = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
            tok_in += response.usage.input_tokens
            tok_out += response.usage.output_tokens

            if verbose:
                print(f"\n--- step {step} --- {response.stop_reason} "
                      f"(running total ${spent():.4f})")

            finished = _final_answer(response)
            if finished is not None:
                answer, stopped = finished
                break

            _handle_tool_calls(messages, response, run_id, step, approve_all, verbose)

    except BaseException as e:  # includes Ctrl-C
        stopped = "crashed"
        answer = f"[crashed: {type(e).__name__}: {e}]"
        raise

    finally:  # a crashed run must still close its row and flush its trace
        run = Run(
            run_id=run_id,
            answer=answer,
            steps=step,
            tokens_in=tok_in,
            tokens_out=tok_out,
            cost_usd=spent(),
            seconds=time.monotonic() - started,
            stopped_because=stopped,
        )
        db.finish_run(run)
        get_client().flush()

    return run


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is 7 to the power of 150? Exact number."
    result = run_agent(question)
    print(f"\nANSWER: {result.answer}")
    print(f"\nsteps={result.steps}  tokens={result.tokens_in}/{result.tokens_out}  "
          f"cost=${result.cost_usd:.5f}  {result.seconds:.1f}s  "
          f"stopped={result.stopped_because}")
