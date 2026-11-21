"""Tool registry: schema the model sees + Python function that runs it."""
from datetime import datetime, timezone

TOOLS = [
    {
        "name": "calculator",
        "description": "Evaluate a basic arithmetic expression, e.g. '2350 * 0.17'.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "utc_now",
        "description": "Get the current date and time in UTC.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def calculator(expression: str) -> str:
    if not set(expression) <= set("0123456789.+-*/() "):
        raise ValueError("Only numbers and + - * / ( ) are allowed")
    return str(eval(expression, {"__builtins__": {}}))  # restricted charset above


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


HANDLERS = {"calculator": calculator, "utc_now": utc_now}
