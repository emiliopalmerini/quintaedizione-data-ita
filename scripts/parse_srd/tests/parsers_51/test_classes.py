# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for classes parser — SRD 5.1."""

from __future__ import annotations

from ...classify import SpanRole
from ...parsers_51.classes import parse_classes
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Classi", (8, 59), "classes.json", "classes")


class TestParseClasses51:
    """5.1: H1(ClassName) > H2("Privilegi di classe") > H3(features)."""

    def test_finds_barbaro_at_h1(self):
        tree = [
            HeadingNode(
                title="Barbaro", level=1,
                content=[], children=[
                    HeadingNode(
                        title="Privilegi di classe", level=2,
                        content=[para("Dado Vita | D12 per ogni livello",
                                      SpanRole.SIDEBAR)],
                        children=[
                            HeadingNode(
                                title="Punti ferita", level=5,
                                content=[para("Dadi Vita: 1d12 per livello")],
                                children=[],
                            ),
                            HeadingNode(
                                title="Ira", level=3,
                                content=[para("Il barbaro entra in furia.")],
                                children=[],
                            ),
                            HeadingNode(
                                title="Difesa Senza Armatura", level=3,
                                content=[para("Finché non indossa armatura.")],
                                children=[],
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

    def test_extracts_features_at_h3(self):
        tree = [
            HeadingNode(
                title="Barbaro", level=1,
                content=[], children=[
                    HeadingNode(
                        title="Privilegi di classe", level=2,
                        content=[],
                        children=[
                            HeadingNode(
                                title="Ira", level=3,
                                content=[para("Il barbaro entra in furia.")],
                                children=[],
                            ),
                            HeadingNode(
                                title="Attacco Irruento", level=3,
                                content=[para("L'avventatezza del barbaro.")],
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_classes(_section(), [], tree)
        assert len(result) == 1
        features = result[0]["features"]
        assert len(features) >= 2
        names = [f["name"] for f in features]
        assert "Ira" in names
        assert "Attacco Irruento" in names

    def test_finds_subclass_under_separate_h2(self):
        tree = [
            HeadingNode(
                title="Guerriero", level=1,
                content=[], children=[
                    HeadingNode(
                        title="Privilegi di classe", level=2,
                        content=[],
                        children=[
                            HeadingNode(
                                title="Archetipo Marziale", level=3,
                                content=[para("A livello 3, scegli un archetipo.")],
                                children=[],
                            ),
                        ],
                    ),
                    HeadingNode(
                        title="Archetipi Marziali", level=2,
                        content=[para("Intro text")],
                        children=[
                            HeadingNode(
                                title="Campione", level=3,
                                content=[para("Il campione si concentra.")],
                                children=[
                                    HeadingNode(
                                        title="Critico Migliorato", level=5,
                                        content=[para("I tuoi attacchi criccano con 19.")],
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
        assert result[0]["name"] == "Guerriero"
        subclasses = result[0]["subclasses"]
        assert len(subclasses) == 1
        assert subclasses[0]["name"] == "Campione"

    def test_multiple_classes(self):
        tree = [
            HeadingNode(
                title="Barbaro", level=1,
                content=[], children=[
                    HeadingNode(title="Privilegi di classe", level=2,
                                content=[], children=[]),
                ],
            ),
            HeadingNode(
                title="Bardo", level=1,
                content=[], children=[
                    HeadingNode(title="Privilegi di classe", level=2,
                                content=[], children=[]),
                ],
            ),
        ]
        result = parse_classes(_section(), [], tree)
        assert len(result) == 2
        names = [c["name"] for c in result]
        assert "Barbaro" in names
        assert "Bardo" in names
