# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for 5.1 subclass detection inside 'Privilegi di classe'."""

from __future__ import annotations

from ...parsers_51.classes import parse_classes
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Classi", (8, 59), "classes.json", "classes")


class TestInlineSubclass51:
    """5.1 subclasses nested inside 'Privilegi di classe' as H3."""

    def test_barbaro_berserker(self):
        tree = [
            HeadingNode(
                title="Barbaro", level=1, content=[], children=[
                    HeadingNode(
                        title="Privilegi di classe", level=2, content=[], children=[
                            HeadingNode(
                                title="Ira", level=3,
                                content=[para("Furia")], children=[],
                            ),
                            HeadingNode(
                                title="Cammino Primordiale", level=3,
                                content=[para("A livello 3, scegli un cammino.")], children=[],
                            ),
                            HeadingNode(
                                title="Cammino del Berserker", level=3,
                                content=[para("Il berserker entra in frenesia.")],
                                children=[
                                    HeadingNode(
                                        title="Frenesia", level=5,
                                        content=[para("Quando entri in ira...")], children=[],
                                    ),
                                    HeadingNode(
                                        title="Ira Incontenibile", level=5,
                                        content=[para("A partire dal 6° livello...")], children=[],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_classes(_section(), [], tree)
        barbaro = result[0]
        assert barbaro["name"] == "Barbaro"
        feature_names = [f["name"] for f in barbaro["features"]]
        assert "Cammino del Berserker" not in feature_names
        assert "Ira" in feature_names
        assert len(barbaro["subclasses"]) == 1
        assert barbaro["subclasses"][0]["name"] == "Cammino del Berserker"
        sc_features = barbaro["subclasses"][0]["features"]
        sc_feat_names = [f["name"] for f in sc_features]
        assert "Frenesia" in sc_feat_names

    def test_chierico_dominio_vita(self):
        tree = [
            HeadingNode(
                title="Chierico", level=1, content=[], children=[
                    HeadingNode(
                        title="Privilegi di classe", level=2, content=[], children=[
                            HeadingNode(
                                title="Incantesimi", level=3,
                                content=[para("Il chierico è un incantatore.")],
                                children=[
                                    HeadingNode(title="Trucchetti", level=5,
                                                content=[para("Conosci 3 trucchetti.")],
                                                children=[]),
                                ],
                            ),
                            HeadingNode(
                                title="Dominio della Vita", level=3,
                                content=[para("Il dominio della Vita si concentra.")],
                                children=[
                                    HeadingNode(title="Competenza Bonus", level=5,
                                                content=[para("Competenza armature pesanti.")],
                                                children=[]),
                                    HeadingNode(title="Discepolo della Vita", level=5,
                                                content=[para("Le cure sono potenziate.")],
                                                children=[]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_classes(_section(), [], tree)
        chierico = result[0]
        feature_names = [f["name"] for f in chierico["features"]]
        assert "Dominio della Vita" not in feature_names
        assert "Incantesimi" in feature_names
        assert len(chierico["subclasses"]) == 1
        assert chierico["subclasses"][0]["name"] == "Dominio della Vita"

    def test_incantesimi_not_a_subclass(self):
        tree = [
            HeadingNode(
                title="Bardo", level=1, content=[], children=[
                    HeadingNode(
                        title="Privilegi di classe", level=2, content=[], children=[
                            HeadingNode(
                                title="Incantesimi", level=3,
                                content=[para("Il bardo è un incantatore.")],
                                children=[
                                    HeadingNode(title="Trucchetti", level=5,
                                                content=[para("Conosci 2 trucchetti.")],
                                                children=[]),
                                ],
                            ),
                            HeadingNode(
                                title="Collegio della Sapienza", level=3,
                                content=[para("Il collegio della sapienza raccoglie...")],
                                children=[
                                    HeadingNode(title="Competenze bonus", level=5,
                                                content=[para("Tre competenze a scelta.")],
                                                children=[]),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_classes(_section(), [], tree)
        bardo = result[0]
        feature_names = [f["name"] for f in bardo["features"]]
        assert "Incantesimi" in feature_names
        assert len(bardo["subclasses"]) == 1
        assert bardo["subclasses"][0]["name"] == "Collegio della Sapienza"
