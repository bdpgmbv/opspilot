"""Step 4: run the tool and send the answer back."""

import anthropic

from opspilot.config import MODEL, anthropic_key
from opspilot.tools import CALCULATOR_SCHEMA, ToolError, calculator

# QUESTION = "What is 18.5% of 2400?"
# QUESTION = "What is 5 divided by 0?"
QUESTION = "What is 7 to the power of 150? Give me the exact number."


def main():
    client = anthropic.Anthropic(api_key=anthropic_key())
    messages = [{"role": "user", "content": QUESTION}]

    # --- turn 1: Claude asks for the tool ---
    first = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[CALCULATOR_SCHEMA],
        messages=messages,
    )
    print("turn 1 stop_reason:", first.stop_reason)

    tool_uses = [b for b in first.content if b.type == "tool_use"]
    if not tool_uses:
        print("Claude answered without a tool. Nothing to send back.")
        return

    # Put Claude's request into the history, exactly as it came back
    messages.append({"role": "assistant", "content": first.content})

    # --- we run the function on our own machine ---
    results = []
    for block in tool_uses:
        try:
            output = calculator(**block.input)
            is_error = False
        except (ToolError, TypeError) as e:
            output = f"Error: {e}"
            is_error = True

        print(f"ran {block.name} -> {output}")

        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,     # must match turn 1 exactly
            "content": output,
            "is_error": is_error,
        })

    # Every result goes back in ONE user message
    messages.append({"role": "user", "content": results})

    # --- turn 2: Claude answers using the result ---
    second = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[CALCULATOR_SCHEMA],
        messages=messages,
    )
    print("turn 2 stop_reason:", second.stop_reason)

    for block in second.content:
        if block.type == "text":
            print("\nANSWER:", block.text)
        elif block.type == "tool_use":
            print("\nClaude asked for ANOTHER tool call:")
            print("   name :", block.name)
            print("   input:", block.input)
            print("   (our script ends here — this is why Level 1 needs a loop)")

    # --- cost log (page 1 of the brief asks for one) ---
    tok_in = first.usage.input_tokens + second.usage.input_tokens
    tok_out = first.usage.output_tokens + second.usage.output_tokens
    cost = tok_in / 1e6 * 4.00 + tok_out / 1e6 * 20.00
    print(f"\ntokens in={tok_in} out={tok_out}  cost=${cost:.5f}")


if __name__ == "__main__":
    main()