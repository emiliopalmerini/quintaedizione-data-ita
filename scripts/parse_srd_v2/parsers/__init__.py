"""Typed entity parsers for parser v2."""

from __future__ import annotations

from typing import Any, Callable

from .classi import parse_classi
from .equipaggiamento import parse_equipaggiamento
from .incantesimi import parse_incantesimi
from .origini import parse_origini
from .result import ParseResult
from .specie import parse_specie
from .talenti import parse_talenti


Parser = Callable[[dict[str, Any], str], ParseResult]

PARSERS: dict[str, Parser] = {
    "classi": parse_classi,
    "origini": parse_origini,
    "specie": parse_specie,
    "talenti": parse_talenti,
    "equipaggiamento": parse_equipaggiamento,
    "incantesimi": parse_incantesimi,
}


def get_parser(name: str) -> Parser | None:
    """Return a parser by name."""

    return PARSERS.get(name)
