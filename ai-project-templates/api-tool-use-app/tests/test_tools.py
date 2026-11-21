import pytest

from tool_app.tools import calculator


def test_calculator():
    assert calculator("12 * 7") == "84"


def test_calculator_rejects_code():
    with pytest.raises(ValueError):
        calculator("__import__('os')")
