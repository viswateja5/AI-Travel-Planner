from __future__ import annotations

from typing import Any


def to_title_case(value: str) -> str:
    return " ".join(word.capitalize() for word in value.replace("_", " ").split())


def ensure_directory(path: str | Any) -> None:
    from pathlib import Path

    Path(path).mkdir(parents=True, exist_ok=True)


def format_currency(value: float, currency: str = "USD") -> str:
    return f"{currency} {value:,.2f}"
