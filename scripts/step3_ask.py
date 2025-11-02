"""Step 3: send one tool to Claude and look at what comes back."""

import anthropic

from opspilot.config import MODEL, anthropic_key

from opspilot.tools import CALCULATOR_SCHEMA

QUESTION = "What is 18.5% of 2400?"


def main():
    client = anthropic.Anthropic(api_key=anthropic_key())

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[CALCULATOR_SCHEMA],          # the menu
        messages=[{"role": "user", "content": QUESTION}],
    )

    print("stop_reason:", response.stop_reason)
    print()

    for block in response.content:
        if block.type == "thinking":
            print("[thinking] (Claude reasoning to itself)")
        elif block.type == "text":
            print("[text]", block.text)
        elif block.type == "tool_use":
            print("[tool_use]")
            print("   id    :", block.id)
            print("   name  :", block.name)
            print("   input :", block.input)

    print()
    print("tokens in:", response.usage.input_tokens,
          " out:", response.usage.output_tokens)


if __name__ == "__main__":
    main()