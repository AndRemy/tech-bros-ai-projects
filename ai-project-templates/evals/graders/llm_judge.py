"""LLM-as-judge: Claude grades the output against the case rubric."""
import os

import anthropic

PROMPT = """Grade the RESPONSE against the RUBRIC.
<question>{input}</question>
<rubric>{rubric}</rubric>
<response>{output}</response>
Think briefly, then end with exactly one line: VERDICT: PASS or VERDICT: FAIL"""


def judge(output: str, case: dict) -> tuple[bool, str]:
    if not case.get("rubric"):
        return True, "no rubric"
    msg = anthropic.Anthropic().messages.create(
        model=os.getenv("JUDGE_MODEL", "claude-opus-5-5"),
        max_tokens=400,
        messages=[{"role": "user", "content": PROMPT.format(output=output, **case)}],
    )
    text = msg.content[0].text
    return "VERDICT: PASS" in text, text.strip().splitlines()[-1]
