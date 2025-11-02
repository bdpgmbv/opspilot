"""Step 7: the same three tools, sent to OpenAI."""

import json

import openai

from opspilot.config import OPENAI_MODEL, openai_key
from opspilot.tools import TOOL_SCHEMAS, run_tool

QUESTION = "What's the weather in Paris in fahrenheit, and what is 18.5% of 2400?"


def to_openai_tools(schemas):
    """Translate our tool schemas into OpenAI's shape. This IS the lesson."""
    return [
        {
            "type": "function",
            "name": s["name"],
            "description": s["description"],
            "parameters": s["input_schema"],   # Anthropic calls this input_schema
        }
        for s in schemas
    ]


def main():
    client = openai.OpenAI(api_key=openai_key())
    conversation = [{"role": "user", "content": QUESTION}]

    # --- turn 1 ---
    first = client.responses.create(
        model=OPENAI_MODEL,
        input=conversation,
        tools=to_openai_tools(TOOL_SCHEMAS),
    )

    calls = [item for item in first.output if item.type == "function_call"]
    print(f"OpenAI asked for {len(calls)} tool call(s):")
    for c in calls:
        print(f"   {c.name}({c.arguments})   <- note: a STRING, not a dict")

    if not calls:
        print("\nANSWER:", first.output_text)
        return

    # Keep everything OpenAI sent, then append our results to the same list
    conversation += first.output

    print()
    for c in calls:
        args = json.loads(c.arguments)          # you must parse it yourself
        text, is_error = run_tool(c.name, args)
        print(f"ran {c.name} -> {text}")

        conversation.append({
            "type": "function_call_output",
            "call_id": c.call_id,               # not 'id' — 'call_id'
            "output": text,                     # no is_error flag exists here
        })

    # --- turn 2 ---
    second = client.responses.create(
        model=OPENAI_MODEL,
        input=conversation,
        tools=to_openai_tools(TOOL_SCHEMAS),
    )
    print("\nANSWER:", second.output_text)

    tok_in = first.usage.input_tokens + second.usage.input_tokens
    tok_out = first.usage.output_tokens + second.usage.output_tokens
    print(f"\ntokens in={tok_in} out={tok_out}")


if __name__ == "__main__":
    main()