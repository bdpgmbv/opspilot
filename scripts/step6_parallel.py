import anthropic

from opspilot.config import MODEL, anthropic_key
from opspilot.tools import TOOL_SCHEMAS, run_tool

QUESTION = "What's the weather in Paris in fahrenheit, and what is 18.5% of 2400?"


def main():
    client = anthropic.Anthropic(api_key=anthropic_key())
    messages = [{"role": "user", "content": QUESTION}]

    # --- turn 1 ---
    first = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=TOOL_SCHEMAS,          # all three now
        messages=messages,
    )
    print("turn 1 stop_reason:", first.stop_reason)

    tool_uses = [b for b in first.content if b.type == "tool_use"]
    print(f"\nClaude asked for {len(tool_uses)} tool call(s) in ONE message:")
    for b in tool_uses:
        print(f"   {b.name}({b.input})")

    messages.append({"role": "assistant", "content": first.content})

    # --- run them all ---
    print()
    results = []
    for b in tool_uses:
        text, is_error = run_tool(b.name, b.input)
        print(f"ran {b.name} -> {text}")
        results.append({
            "type": "tool_result",
            "tool_use_id": b.id,
            "content": text,
            "is_error": is_error,
        })

    # --- all results go back in ONE message ---
    messages.append({"role": "user", "content": results})
    print(f"\nsent {len(results)} result(s) back in ONE message")

    # --- turn 2 ---
    second = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=TOOL_SCHEMAS,
        messages=messages,
    )
    print("turn 2 stop_reason:", second.stop_reason)
    for b in second.content:
        if b.type == "text":
            print("\nANSWER:", b.text)

    tok_in = first.usage.input_tokens + second.usage.input_tokens
    tok_out = first.usage.output_tokens + second.usage.output_tokens
    cost = tok_in / 1e6 * 4.00 + tok_out / 1e6 * 20.00
    print(f"\ntokens in={tok_in} out={tok_out}  cost=${cost:.5f}")


if __name__ == "__main__":
    main()