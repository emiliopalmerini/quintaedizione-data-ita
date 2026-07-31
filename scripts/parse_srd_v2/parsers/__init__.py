"""Typed entity parsers for parser v2."""

from __future__ import annotations

from typing import Any, Callable

from .classi import parse_classi
from .equipaggiamento import parse_equipaggiamento
from .glossario_delle_regole import parse_glossario
from .incantesimi import parse_incantesimi
from .mostri import parse_animali, parse_mostri
from .origini import parse_origini
from .oggetti_magici import parse_oggetti_magici
from .regole import parse_regole
from .result import ParseResult
from .specie import parse_specie
from .talenti import parse_talenti


Parser = Callable[[dict[str, Any], str], ParseResult]

PARSERS: dict[str, Parser] = {
    "classi": parse_classi,
    "origini": parse_origini,
    "oggetti_magici": parse_oggetti_magici,
    "regole": parse_regole,
    "specie": parse_specie,
    "talenti": parse_talenti,
    "equipaggiamento": parse_equipaggiamento,
    "incantesimi": parse_incantesimi,
    "mostri": parse_mostri,
    "animali": parse_animali,
    "glossario_delle_regole": parse_glossario,
}


def get_parser(name: str) -> Parser | None:
    """Return a parser by name."""

    return PARSERS.get(name)
