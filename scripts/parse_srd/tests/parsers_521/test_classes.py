# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for classes parser — SRD 5.2.1."""

from __future__ import annotations

from ...classify import SpanRole
from ...parsers.classes import parse_classes
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Classi", (8, 59), "classes.json", "classes")


class TestParseClasses521:
    """5.2.1: H1("Classi") > H2(ClassName) > H4(features/subclasses)."""

    def test_finds_barbaro(self):
        tree = [
            HeadingNode(
                title="Classi", level=1,
                content=[], children=[
                    HeadingNode(
                        title="Barbaro", level=2,
                        content=[para("Dado Vita | D12 per ogni livello",
                                      SpanRole.SIDEBAR)],
                        children=[
                            HeadingNode(
                                title="Privilegi di classe del Barbaro", level=4,
                                content=[], children=[
                                    HeadingNode(
                                        title="Livello 1: Ira", level=5,
                                        content=[para("Il barbaro entra in uno stato di furia.")],
                                        children=[],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_classes(_section(), [], tree)
        assert len(result) == 1
        assert result[0]["name"] == "Barbaro"
        assert result[0]["hit_die"] == "d12"
        assert len(result[0]["features"]) == 1
        assert result[0]["features"][0]["name"] == "Ira"
