# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for backgrounds parser — SRD 5.2.1."""

from __future__ import annotations

from ...classify import SpanRole
from ...parsers.backgrounds import parse_backgrounds
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Backgrounds", (65, 67), "backgrounds.json", "backgrounds")


class TestParseBackgrounds521:
    """5.2.1: H2 > H4("Descrizioni") > H5(BackgroundName)."""

    def test_finds_accolito(self):
        tree = [
            HeadingNode(
                title="Background dei personaggi", level=2,
                content=[], children=[
                    HeadingNode(
                        title="Descrizioni dei background", level=4,
                        content=[], children=[
                            HeadingNode(
                                title="Accolito", level=5,
                                content=[
                                    para("Punteggi di caratteristica: +1 Sag, +1 Int, +1 Car",
                                         SpanRole.TABLE_HEADER),
                                    para("Talento: Iniziato alla Magia (Divina)",
                                         SpanRole.TABLE_HEADER),
                                    para("Un accolito ha dedicato la propria vita al servizio."),
                                ],
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_backgrounds(_section(), [], tree)
        assert len(result) == 1
        assert result[0]["name"] == "Accolito"
