# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for backgrounds parser — SRD 5.1."""

from __future__ import annotations

from ...classify import SpanRole
from ...parsers_51.backgrounds import parse_backgrounds
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Backgrounds", (65, 67), "backgrounds.json", "backgrounds")


class TestParseBackgrounds51:
    """5.1: H2("Background") > H3(BackgroundName)."""

    def test_finds_accolito_at_h3(self):
        tree = [
            HeadingNode(
                title="Background", level=2,
                content=[para("Ogni storia ha un inizio.")],
                children=[
                    HeadingNode(
                        title="Competenze", level=5,
                        content=[para("Le competenze del background.")],
                        children=[],
                    ),
                    HeadingNode(
                        title="Accolito", level=3,
                        content=[
                            para("Competenze nelle abilità: Intuizione, Religione",
                                 SpanRole.BODY_BOLD),
                            para("Linguaggi: Due a scelta",
                                 SpanRole.BODY_BOLD),
                            para("Equipaggiamento: Un simbolo sacro",
                                 SpanRole.BODY_BOLD),
                            para("Un accolito ha dedicato la propria vita."),
                        ],
                        children=[
                            HeadingNode(
                                title="Privilegio: Rifugio dei Fedeli", level=5,
                                content=[para("L'accolito può trovare rifugio.")],
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
        assert "Rifugio dei Fedeli" in result[0]["description"]

    def test_extracts_skills_from_body_bold(self):
        """5.1 uses BODY_BOLD for metadata, not TABLE_HEADER."""
        tree = [
            HeadingNode(
                title="Background", level=2,
                content=[],
                children=[
                    HeadingNode(
                        title="Accolito", level=3,
                        content=[
                            para("Competenze nelle abilità: Intuizione, Religione",
                                 SpanRole.BODY_BOLD),
                            para("Equipaggiamento: Un simbolo sacro",
                                 SpanRole.BODY_BOLD),
                            para("Un accolito ha dedicato la vita."),
                        ],
                        children=[],
                    ),
                ],
            ),
        ]
        result = parse_backgrounds(_section(), [], tree)
        assert result[0]["skill_proficiencies"] == "Intuizione, Religione"
        assert result[0]["equipment"] == "Un simbolo sacro"
