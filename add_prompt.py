#!/usr/bin/env python3
"""
Add a prompt to prompts.md in the required format.
Usage: python add_prompt.py "Your prompt text here"
"""

import sys
from pathlib import Path

PROMPTS_FILE = Path(__file__).parent / "prompts.md"


def get_next_number():
    """Get the next prompt number from the file."""
    if not PROMPTS_FILE.exists():
        return 1
    content = PROMPTS_FILE.read_text()
    count = 0
    for line in content.splitlines():
        if line.strip().startswith("Prompt ") and " : " in line:
            count += 1
    return count + 1


def add_prompt(prompt_text: str) -> None:
    num = get_next_number()
    entry = f"Prompt {num} : {prompt_text}\n------\n"
    content = PROMPTS_FILE.read_text() if PROMPTS_FILE.exists() else ""
    new_content = (content.rstrip() + "\n\n" + entry) if content.strip() else entry
    PROMPTS_FILE.write_text(new_content, encoding="utf-8")
    print(f"Added Prompt {num} to {PROMPTS_FILE.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python add_prompt.py "Your prompt text here"')
        sys.exit(1)
    prompt = " ".join(sys.argv[1:])
    add_prompt(prompt)
