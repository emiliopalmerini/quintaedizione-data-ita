# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for equipment parser — SRD 5.1 sequential table parsing."""

from __future__ import annotations

from ...classify import SpanRole
from ...parsers_51.equipment import parse_equipment
from ...section_split import SectionDef
from ..helpers import HeadingNode, para


def _section() -> SectionDef:
    return SectionDef("Equipaggiamento", (68, 84), "equipment.json", "equipment")


class TestParseArmorFromSequentialParagraphs:
    """5.1: armor data as sequential TABLE_HEADER_SMALL + TABLE_BODY paragraphs."""

    def test_extracts_armor_items(self):
        content = [
            para("Descrizione armature.", SpanRole.BODY),
            para("Armature", SpanRole.UNKNOWN),
            para("Armatura", SpanRole.TABLE_HEADER_SMALL),
            para("Costo", SpanRole.TABLE_HEADER_SMALL),
            para("Classe Armatura (CA)", SpanRole.TABLE_HEADER_SMALL),
            para("Forza", SpanRole.TABLE_HEADER_SMALL),
            para("Furtività", SpanRole.TABLE_HEADER_SMALL),
            para("Peso", SpanRole.TABLE_HEADER_SMALL),
            para("Armature leggere", SpanRole.UNKNOWN),
            para("Imbottita", SpanRole.TABLE_BODY),
            para("5 mo", SpanRole.TABLE_BODY),
            para("11 + modificatore di Des", SpanRole.TABLE_BODY),
            para("—", SpanRole.TABLE_BODY),
            para("Svantaggio", SpanRole.TABLE_BODY),
            para("4 kg", SpanRole.TABLE_BODY),
            para("Cuoio", SpanRole.TABLE_BODY),
            para("10 mo", SpanRole.TABLE_BODY),
            para("11 + modificatore di Des", SpanRole.TABLE_BODY),
            para("—", SpanRole.TABLE_BODY),
            para("—", SpanRole.TABLE_BODY),
            para("5 kg", SpanRole.TABLE_BODY),
        ]
        tree = [
            HeadingNode(title="Equipaggiamento", level=1, content=[], children=[
                HeadingNode(title="Armature", level=2, content=[], children=[
                    HeadingNode(title="Armature pesanti", level=3,
                                content=content, children=[]),
                ]),
            ]),
        ]
        result = parse_equipment(_section(), [], tree)
        armor = [i for i in result if i["category"] == "armor"]
        assert len(armor) >= 2
        names = [i["name"] for i in armor]
        assert "Imbottita" in names
        assert "Cuoio" in names

        imbottita = next(i for i in armor if i["name"] == "Imbottita")
        assert imbottita["subcategory"] == "Armature leggere"
        assert "11 + modificatore di Des" in imbottita["properties"].get("classe_armatura", "")


class TestParseWeaponsFromSequentialParagraphs:
    """5.1: weapon data as sequential TABLE_HEADER_SMALL + TABLE_BODY paragraphs."""

    def test_extracts_weapon_items(self):
        content = [
            para("Nome", SpanRole.TABLE_HEADER_SMALL),
            para("Costo", SpanRole.TABLE_HEADER_SMALL),
            para("Danni", SpanRole.TABLE_HEADER_SMALL),
            para("Peso", SpanRole.TABLE_HEADER_SMALL),
            para("Proprietà", SpanRole.TABLE_HEADER_SMALL),
            para("Armi semplici da mischia", SpanRole.UNKNOWN),
            para("Bastone ferrato", SpanRole.TABLE_BODY),
            para("2 ma", SpanRole.TABLE_BODY),
            para("1d6 contundenti", SpanRole.TABLE_BODY),
            para("2 kg", SpanRole.TABLE_BODY),
            para("Versatile (1d8)", SpanRole.TABLE_BODY),
        ]
        tree = [
            HeadingNode(title="Equipaggiamento", level=1, content=[], children=[
                HeadingNode(title="Armi", level=2, content=[], children=[
                    HeadingNode(title="Competenza nelle armi", level=3,
                                content=content, children=[]),
                ]),
            ]),
        ]
        result = parse_equipment(_section(), [], tree)
        weapons = [i for i in result if i["category"] == "weapons"]
        assert len(weapons) >= 1
        assert weapons[0]["name"] == "Bastone ferrato"
        assert weapons[0]["properties"].get("danni") == "1d6 contundenti"
