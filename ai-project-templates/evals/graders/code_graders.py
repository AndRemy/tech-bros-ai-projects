"""Deterministic graders: return (passed, reason)."""


def contains_all(output: str, case: dict) -> tuple[bool, str]:
    missing = [s for s in case.get("must_contain", []) if s.lower() not in output.lower()]
    return (not missing, f"missing: {missing}" if missing else "ok")
