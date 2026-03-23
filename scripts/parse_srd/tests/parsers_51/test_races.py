# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for races parser (5.1 → species.json)."""

from __future__ import annotations

from ...parsers_51.races import parse_races
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Razze", (2, 7), "species.json", "races")


class TestParseRaces:
    """5.1: H1(Razze) > H2(RaceName) > H3(Tratti) with traits as bold-italic."""

    def test_finds_race(self):
        tree = [
            HeadingNode(title="Razze", level=1, content=[], children=[
                HeadingNode(title="Elfo", level=2, content=[], children=[
                    HeadingNode(
                        title="Tratti degli elfi", level=3,
                        content=[
                            para("_**Incremento dei punteggi di caratteristica.**_ "
                                 "Il punteggio di Destrezza aumenta di 2."),
                            para("_**Velocità.**_ La velocità base è di 9 metri."),
                        ],
                        children=[],
                    ),
                ]),
            ]),
        ]
        result = parse_races(_section(), [], tree)
        assert len(result) == 1
        assert result[0]["name"] == "Elfo"
        assert len(result[0]["traits"]) >= 2

    def test_extracts_subrace(self):
        tree = [
            HeadingNode(title="Razze", level=1, content=[], children=[
                HeadingNode(title="Elfo", level=2, content=[], children=[
                    HeadingNode(
                        title="Tratti degli elfi", level=3,
                        content=[
                            para("_**Velocità.**_ 9 metri."),
                        ],
                        children=[
                            HeadingNode(
                                title="Elfo alto", level=5,
                                content=[
                                    para("_**Incremento dei punteggi.**_ Int +1."),
                                    para("_**Trucchetto.**_ Conosci un trucchetto."),
                                ],
                                children=[],
                            ),
                        ],
                    ),
                ]),
            ]),
        ]
        result = parse_races(_section(), [], tree)
        assert len(result) == 1
        desc = result[0]["description"]
        assert "Elfo alto" in desc

    def test_multiple_races(self):
        tree = [
            HeadingNode(title="Razze", level=1, content=[], children=[
                HeadingNode(title="Elfo", level=2, content=[], children=[
                    HeadingNode(title="Tratti degli elfi", level=3,
                                content=[para("Tratti.")], children=[]),
                ]),
                HeadingNode(title="Nano", level=2, content=[], children=[
                    HeadingNode(title="Tratti dei nani", level=3,
                                content=[para("Tratti.")], children=[]),
                ]),
                HeadingNode(title="Umano", level=2, content=[], children=[
                    HeadingNode(title="Tratti degli umani", level=3,
                                content=[para("Tratti.")], children=[]),
                ]),
            ]),
        ]
        result = parse_races(_section(), [], tree)
        assert len(result) == 3
        names = [r["name"] for r in result]
        assert "Elfo" in names
        assert "Nano" in names
        assert "Umano" in names
