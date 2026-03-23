# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for monster parser — SRD 5.1 body-font stat blocks."""

from __future__ import annotations

from ...classify import SpanRole
from ...parsers_51.monsters import parse_monsters
from ...section_split import SectionDef
from ..helpers import HeadingNode, para, span, multi_para


def _section() -> SectionDef:
    return SectionDef("Mostri", (298, 410), "monsters.json", "monsters")


def _aboleth_content():
    """Minimal Aboleth stat block in 5.1 format."""
    return [
        para("Aberrazione Grande, legale malvagio", SpanRole.BODY_ITALIC),
        multi_para([
            span("Classe Armatura", SpanRole.BODY_BOLD),
            span(" 17 (armatura naturale)", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        multi_para([
            span("Punti Ferita", SpanRole.BODY_BOLD),
            span(" 135 (18d10 + 36)", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        multi_para([
            span("Velocità", SpanRole.BODY_BOLD),
            span(" 3 m, nuotare 12 m", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        para("FOR", SpanRole.BODY_BOLD),
        para("DES", SpanRole.BODY_BOLD),
        para("COS", SpanRole.BODY_BOLD),
        para("INT", SpanRole.BODY_BOLD),
        para("SAG", SpanRole.BODY_BOLD),
        para("CAR", SpanRole.BODY_BOLD),
        para("21 (+5)", SpanRole.SIDEBAR),
        para("9 (-1)", SpanRole.SIDEBAR),
        para("15 (+2) 18 (+4) 15 (+2) 18 (+4)", SpanRole.SIDEBAR),
        multi_para([
            span("Tiri Salvezza", SpanRole.BODY_BOLD),
            span(" Cos +6, Int +8, Sag +6", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        multi_para([
            span("Sensi", SpanRole.BODY_BOLD),
            span(" Percezione passiva 20, scurovisione 36 m", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        multi_para([
            span("Linguaggi", SpanRole.BODY_BOLD),
            span(" Gergo delle profondità, telepatia 36 m", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        multi_para([
            span("Sfida", SpanRole.BODY_BOLD),
            span(" 10 (5.900 PE)", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD),
        multi_para([
            span("Anfibio.", SpanRole.BODY_BOLD_ITALIC),
            span(" L'aboleth può respirare in aria e in acqua.", SpanRole.SIDEBAR),
        ], SpanRole.BODY_BOLD_ITALIC),
    ]


class TestParseMonsters51:
    """5.1: H2(group) > H5(monster) with body-font stat blocks."""

    def test_finds_monster_at_h5(self):
        tree = [
            HeadingNode(
                title="Mostri (A)", level=2, content=[], children=[
                    HeadingNode(
                        title="Aboleth", level=5,
                        content=_aboleth_content(),
                        children=[
                            HeadingNode(
                                title="Azioni", level=6,
                                content=[
                                    multi_para([
                                        span("Multiattacco.", SpanRole.BODY_BOLD_ITALIC),
                                        span(" L'aboleth effettua tre attacchi.", SpanRole.SIDEBAR),
                                    ], SpanRole.BODY_BOLD_ITALIC),
                                ],
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_monsters(_section(), [], tree)
        assert len(result) == 1
        m = result[0]
        assert m["name"] == "Aboleth"
        assert m["type"] == "Aberrazione"
        assert m["size"] == "Grande"
        assert "legale malvagio" in m["alignment"]
        assert "17" in m["ac"]
        assert "135" in m["hp"]
        assert m["cr"] == "10"
        assert len(m["actions"]) >= 1

    def test_grouped_monsters(self):
        tree = [
            HeadingNode(
                title="Mostri (A)", level=2, content=[], children=[
                    HeadingNode(
                        title="Angeli", level=3, content=[], children=[
                            HeadingNode(
                                title="Deva", level=5,
                                content=[
                                    para("Celestiale Medio, legale buono", SpanRole.BODY_ITALIC),
                                    multi_para([
                                        span("Classe Armatura", SpanRole.BODY_BOLD),
                                        span(" 17 (armatura naturale)", SpanRole.SIDEBAR),
                                    ], SpanRole.BODY_BOLD),
                                    multi_para([
                                        span("Punti Ferita", SpanRole.BODY_BOLD),
                                        span(" 136 (16d8 + 64)", SpanRole.SIDEBAR),
                                    ], SpanRole.BODY_BOLD),
                                    multi_para([
                                        span("Velocità", SpanRole.BODY_BOLD),
                                        span(" 9 m, volare 27 m", SpanRole.SIDEBAR),
                                    ], SpanRole.BODY_BOLD),
                                    multi_para([
                                        span("Sfida", SpanRole.BODY_BOLD),
                                        span(" 10 (5.900 PE)", SpanRole.SIDEBAR),
                                    ], SpanRole.BODY_BOLD),
                                ],
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ]
        result = parse_monsters(_section(), [], tree)
        assert len(result) == 1
        assert result[0]["name"] == "Deva"
        assert result[0]["group"] == "Angeli"
