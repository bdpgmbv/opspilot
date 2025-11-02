"""Level 1: the agent loop, with limits and a cost log."""

import sys
import time
import uuid
import anthropic

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from opspilot import db
from opspilot.config import MODEL, PRICE_IN, PRICE_OUT, anthropic_key
from opspilot.tools import RISKY_TOOLS, TOOL_SCHEMAS, run_tool


MAX_STEPS = 10
MAX_COST_USD = 0.25
PARALLEL = True
REQUIRE_APPROVAL = True


@dataclass
class Run:
    run_id: str
    answer: str
    steps: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    seconds: float
    stopped_because: str


def run_agent(question: str, verbose: bool = True) -> Run:
    client = anthropic.Anthropic(api_key=anthropic_key())
    messages = [{"role": "user", "content": question}]

    run_id = uuid.uuid4().hex[:8]
    db.start_run(run_id, question)

    started = time.monotonic()
    tok_in = tok_out = 0
    answer = f"[gave up after {MAX_STEPS} steps]"
    stopped = "step_limit"
    step = 0

    def spent() -> float:
        return tok_in / 1e6 * PRICE_IN + tok_out / 1e6 * PRICE_OUT

    for step in range(1, MAX_STEPS + 1):
        
        # budget check BEFORE spending, not after
        if spent() >= MAX_COST_USD:
            stopped = "cost_budget"
            answer = f"[stopped: spent ${spent():.4f} of ${MAX_COST_USD} budget]"
            break

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )
        tok_in += response.usage.input_tokens
        tok_out += response.usage.output_tokens

        if verbose:
            print(f"\n--- step {step} --- {response.stop_reason} "
                  f"(running total ${spent():.4f})")

        if response.stop_reason == "end_turn":
            answer = "".join(b.text for b in response.content if b.type == "text")
            stopped = "answered"
            break

        if response.stop_reason != "tool_use":
            answer = f"[stopped: {response.stop_reason}]"
            stopped = response.stop_reason
            break

        messages.append({"role": "assistant", "content": response.content})


        calls = [b for b in response.content if b.type == "tool_use"]

        # Ask one at a time. Never inside a thread.
        approval = {}
        for b in calls:
            if REQUIRE_APPROVAL and b.name in RISKY_TOOLS:
                approval[b.id] = "granted" if _approve(b.name, b.input) else "declined"
            else:
                approval[b.id] = "not_required"

        def run_one(b):
            if approval[b.id] == "declined":
                return ("Error: the human declined this action. Do not retry it.", True)
            return run_tool(b.name, b.input)


        if PARALLEL and len(calls) > 1:
            with ThreadPoolExecutor(max_workers=8) as pool:
                outputs = list(pool.map(run_one, calls))
        else:
            outputs = [run_one(b) for b in calls]


        results = []
        for block, (text, is_error) in zip(calls, outputs):
            if verbose:
                mark = "ERR " if is_error else "    "
                print(f"  {mark}{block.name}({block.input})")
                print(f"       -> {text[:70]}{'... [truncated in log]' if len(text) > 70 else ''}")
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": text,
                "is_error": is_error,
            })
            db.save_event(run_id, step, block.name, block.input,
                          text, is_error, approval[block.id])

        messages.append({"role": "user", "content": results})

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
    return run


def _approve(name: str, tool_input: dict) -> bool:
    print(f"\n  APPROVAL NEEDED -> {name}({tool_input})")
    return input("  allow? [y/N] ").strip().lower() == "y"


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What is 7 to the power of 150? Exact number."
    r = run_agent(q)
    print(f"\nANSWER: {r.answer}")
    print(f"\nsteps={r.steps}  tokens={r.tokens_in}/{r.tokens_out}  "
          f"cost=${r.cost_usd:.5f}  {r.seconds:.1f}s  stopped={r.stopped_because}")