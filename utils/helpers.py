from __future__ import annotations

from typing import Any


def to_title_case(value: str) -> str:
    return " ".join(word.capitalize() for word in value.replace("_", " ").split())


def ensure_directory(path: str | Any) -> None:
    from pathlib import Path

    Path(path).mkdir(parents=True, exist_ok=True)


def _format_indian_number(value: float) -> str:
    magnitude = abs(int(value))
    integer_str = str(magnitude)
    if len(integer_str) <= 3:
        formatted = integer_str
    else:
        last_three = integer_str[-3:]
        remaining = integer_str[:-3]
        if len(remaining) <= 2:
            formatted = f"{remaining},{last_three}"
        else:
            chunk = remaining[:-2]
            tail = remaining[-2:]
            formatted = f"{chunk},{tail},{last_three}"

    decimal_part = abs(value) - magnitude
    if decimal_part:
        return f"{formatted}.{decimal_part:0.2f}".replace(".00", "")
    return formatted


def format_currency(value: float, currency: str = "INR") -> str:
    numeric_value = float(value)
    if currency.upper() == "INR":
        sign = "-" if numeric_value < 0 else ""
        return f"{sign}₹{_format_indian_number(abs(numeric_value))}"
    return f"{currency.upper()} {numeric_value:,.2f}"
