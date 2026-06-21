"""Typed entity parsers for parser v2."""

from __future__ import annotations

from typing import Any, Callable

from .origini import parse_origini


Parser = Callable[[dict[str, Any], str], list[dict[str, Any]]]

PARSERS: dict[str, Parser] = {
    "origini": parse_origini,
}


def get_parser(name: str) -> Parser | None:
    """Return a parser by name."""

    return PARSERS.get(name)
