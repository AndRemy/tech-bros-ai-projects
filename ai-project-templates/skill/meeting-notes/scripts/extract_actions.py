"""Extract action items from raw notes. Usage: python extract_actions.py notes.txt"""
import re
import sys

PATTERN = re.compile(r"^\s*(?:TODO[:\s]|AI:|@\w+)", re.IGNORECASE)


def extract(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if PATTERN.match(line)]


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        for item in extract(f.read()):
            print(f"- [ ] {item}")
