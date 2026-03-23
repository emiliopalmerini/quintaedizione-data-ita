# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for the segments post-processing module."""

from __future__ import annotations

import pytest

from ..segments import (
    Catalogs,
    build_catalogs,
    segmentize_dict,
    segmentize_outputs,
    text_to_segments,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _cats_with_spells() -> Catalogs:
    """Catalogs with a few spells for testing."""
    cats = Catalogs()
    cats.add("spell", {
        "Comunione": "comunione",
        "Rianimare morti": "rianimare-morti",
        "Palla di fuoco": "palla-di-fuoco",
    })
    return cats


def _cats_with_damage_types() -> Catalogs:
    cats = Catalogs()
    cats.add("damage_type", {
        "fuoco": "fuoco",
        "fulmine": "fulmine",
        "freddo": "freddo",
    })
    return cats


def _cats_with_conditions() -> Catalogs:
    cats = Catalogs()
    cats.add("condition", {
        "avvelenato": "avvelenato",
        "paralizzato": "paralizzato",
        "privo di sensi": "privo-di-sensi",
    })
    return cats


def _cats_mixed() -> Catalogs:
    """Catalogs with multiple ref types."""
    cats = Catalogs()
    cats.add("spell", {
        "Comunione": "comunione",
        "Resurrezione": "resurrezione",
    })
    cats.add("damage_type", {
        "fuoco": "fuoco",
    })
    cats.add("condition", {
        "avvelenato": "avvelenato",
    })
    cats.add("ability", {
        "Carisma": "carisma",
    })
    return cats


# ── text_to_segments ────────────────────────────────────────────────────────


class TestTextToSegments:

    def test_empty_string(self):
        cats = _cats_with_spells()
        result = text_to_segments("", cats)
        assert result == []

    def test_no_matches(self):
        cats = _cats_with_spells()
        result = text_to_segments("Nessun riferimento qui", cats)
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "Nessun riferimento qui"

    def test_single_spell_match(self):
        cats = _cats_with_spells()
        result = text_to_segments("Il deva lancia Comunione a volontà", cats)
        assert len(result) == 3
        assert result[0] == {"type": "text", "text": "Il deva lancia "}
        assert result[1] == {"type": "spell", "text": "Comunione", "id": "comunione"}
        assert result[2] == {"type": "text", "text": " a volontà"}

    def test_multiple_matches(self):
        cats = _cats_with_spells()
        result = text_to_segments("Lancia Comunione e Rianimare morti", cats)
        assert len(result) == 4
        assert result[0] == {"type": "text", "text": "Lancia "}
        assert result[1] == {"type": "spell", "text": "Comunione", "id": "comunione"}
        assert result[2] == {"type": "text", "text": " e "}
        assert result[3] == {"type": "spell", "text": "Rianimare morti", "id": "rianimare-morti"}

    def test_match_at_start(self):
        cats = _cats_with_spells()
        result = text_to_segments("Comunione è un incantesimo", cats)
        assert result[0] == {"type": "spell", "text": "Comunione", "id": "comunione"}
        assert result[1] == {"type": "text", "text": " è un incantesimo"}

    def test_match_at_end(self):
        cats = _cats_with_spells()
        result = text_to_segments("L'incantesimo è Comunione", cats)
        assert result[-1] == {"type": "spell", "text": "Comunione", "id": "comunione"}

    def test_damage_type_match(self):
        cats = _cats_with_damage_types()
        result = text_to_segments("Resistenze ai danni: fuoco, fulmine", cats)
        assert len(result) == 4
        assert result[1] == {"type": "damage_type", "text": "fuoco", "id": "fuoco"}
        assert result[3] == {"type": "damage_type", "text": "fulmine", "id": "fulmine"}

    def test_condition_match(self):
        cats = _cats_with_conditions()
        result = text_to_segments("Immune a avvelenato e paralizzato", cats)
        assert any(s["type"] == "condition" and s["id"] == "avvelenato" for s in result)
        assert any(s["type"] == "condition" and s["id"] == "paralizzato" for s in result)

    def test_multi_word_condition(self):
        cats = _cats_with_conditions()
        result = text_to_segments("La creatura è privo di sensi", cats)
        assert any(
            s["type"] == "condition" and s["id"] == "privo-di-sensi"
            for s in result
        )

    def test_case_insensitive(self):
        cats = _cats_with_spells()
        result = text_to_segments("lancia comunione", cats)
        assert any(s["type"] == "spell" and s["id"] == "comunione" for s in result)

    def test_longer_match_takes_priority(self):
        """'Palla di fuoco' (spell) should match before 'fuoco' (damage_type)."""
        cats = Catalogs()
        cats.add("spell", {"Palla di fuoco": "palla-di-fuoco"})
        cats.add("damage_type", {"fuoco": "fuoco"})
        result = text_to_segments("Lancia Palla di fuoco", cats)
        # Should match the full spell name, not just "fuoco"
        refs = [s for s in result if s["type"] != "text"]
        assert len(refs) == 1
        assert refs[0] == {"type": "spell", "text": "Palla di fuoco", "id": "palla-di-fuoco"}

    def test_word_boundary_no_partial_match(self):
        """Should not match 'fuoco' inside 'fuocoso'."""
        cats = _cats_with_damage_types()
        result = text_to_segments("Il materiale fuocoso brucia", cats)
        refs = [s for s in result if s["type"] != "text"]
        assert len(refs) == 0

    def test_mixed_ref_types(self):
        cats = _cats_mixed()
        result = text_to_segments(
            "Lancia Comunione utilizzando Carisma. Immune a avvelenato.",
            cats,
        )
        types = {s["type"] for s in result if s["type"] != "text"}
        assert "spell" in types
        assert "ability" in types
        assert "condition" in types

    def test_preserves_surrounding_text(self):
        cats = _cats_with_spells()
        text = "Il deva può lanciare Comunione 1/giorno"
        result = text_to_segments(text, cats)
        reconstructed = "".join(s["text"] for s in result)
        assert reconstructed == text

    def test_adjacent_matches(self):
        """Two matches separated only by punctuation."""
        cats = _cats_with_damage_types()
        result = text_to_segments("fuoco, fulmine", cats)
        assert result[0] == {"type": "damage_type", "text": "fuoco", "id": "fuoco"}
        assert result[1] == {"type": "text", "text": ", "}
        assert result[2] == {"type": "damage_type", "text": "fulmine", "id": "fulmine"}


# ── Catalogs ────────────────────────────────────────────────────────────────


class TestCatalogs:

    def test_add_and_retrieve(self):
        cats = Catalogs()
        cats.add("spell", {"Comunione": "comunione"})
        entries = cats.all_entries()
        assert len(entries) == 1
        assert entries[0] == ("comunione", "Comunione", "comunione", "spell")

    def test_longest_first_ordering(self):
        cats = Catalogs()
        cats.add("spell", {
            "Fuoco": "fuoco",
            "Palla di fuoco": "palla-di-fuoco",
        })
        entries = cats.all_entries()
        assert entries[0][0] == "palla di fuoco"  # longer first

    def test_multiple_types(self):
        cats = Catalogs()
        cats.add("spell", {"Comunione": "comunione"})
        cats.add("damage_type", {"fuoco": "fuoco"})
        entries = cats.all_entries()
        types = {e[3] for e in entries}
        assert types == {"spell", "damage_type"}


# ── build_catalogs ──────────────────────────────────────────────────────────


class TestBuildCatalogs:

    def test_includes_fixed_catalogs(self):
        cats = build_catalogs({})
        entries = cats.all_entries()
        types = {e[3] for e in entries}
        assert "damage_type" in types
        assert "condition" in types
        assert "ability" in types
        assert "skill" in types
        assert "creature_type" in types

    def test_includes_spells_from_output(self):
        outputs = {
            "spells.json": [
                {"name": "Comunione", "id": "comunione"},
                {"name": "Resurrezione", "id": "resurrezione"},
            ],
        }
        cats = build_catalogs(outputs)
        entries = cats.all_entries()
        spell_ids = {e[2] for e in entries if e[3] == "spell"}
        assert "comunione" in spell_ids
        assert "resurrezione" in spell_ids

    def test_includes_equipment_from_output(self):
        outputs = {
            "equipment.json": [
                {"name": "Spada lunga", "id": "spada-lunga"},
            ],
        }
        cats = build_catalogs(outputs)
        entries = cats.all_entries()
        equip_ids = {e[2] for e in entries if e[3] == "equipment"}
        assert "spada-lunga" in equip_ids

    def test_no_spells_if_not_in_output(self):
        cats = build_catalogs({})
        entries = cats.all_entries()
        assert not any(e[3] == "spell" for e in entries)


# ── segmentize_dict ─────────────────────────────────────────────────────────


class TestSegmentizeDict:

    def test_converts_description_field(self):
        cats = _cats_with_spells()
        d: dict = {"name": "Deva", "description": "Lancia Comunione"}
        segmentize_dict(d, cats)
        assert isinstance(d["description"], list)
        assert any(s["type"] == "spell" for s in d["description"])

    def test_leaves_non_content_fields_alone(self):
        cats = _cats_with_spells()
        d: dict = {"name": "Comunione", "id": "comunione", "level": 5}
        segmentize_dict(d, cats)
        assert d["name"] == "Comunione"
        assert d["id"] == "comunione"
        assert d["level"] == 5

    def test_recurses_into_nested_lists(self):
        cats = _cats_with_spells()
        d: dict = {
            "traits": [
                {"name": "Incantesimi", "description": "Lancia Comunione"}
            ],
        }
        segmentize_dict(d, cats)
        assert isinstance(d["traits"][0]["description"], list)

    def test_converts_resistances(self):
        cats = _cats_with_damage_types()
        d: dict = {"resistances": "fuoco, fulmine"}
        segmentize_dict(d, cats)
        assert isinstance(d["resistances"], list)
        refs = [s for s in d["resistances"] if s["type"] == "damage_type"]
        assert len(refs) == 2

    def test_converts_condition_immunities(self):
        cats = _cats_with_conditions()
        d: dict = {"condition_immunities": "avvelenato, paralizzato"}
        segmentize_dict(d, cats)
        assert isinstance(d["condition_immunities"], list)
        refs = [s for s in d["condition_immunities"] if s["type"] == "condition"]
        assert len(refs) == 2

    def test_converts_benefit_field(self):
        cats = _cats_mixed()
        d: dict = {"benefit": "Ottieni l'incantesimo Comunione"}
        segmentize_dict(d, cats)
        assert isinstance(d["benefit"], list)

    def test_converts_content_field(self):
        cats = _cats_mixed()
        d: dict = {"content": "Il fuoco è un tipo di danno"}
        segmentize_dict(d, cats)
        assert isinstance(d["content"], list)


# ── segmentize_outputs ──────────────────────────────────────────────────────


class TestSegmentizeOutputs:

    def test_full_pipeline(self):
        """End-to-end: build catalogs from output, then segmentize."""
        outputs: dict[str, list] = {
            "spells.json": [
                {
                    "id": "comunione",
                    "name": "Comunione",
                    "description": "Un incantesimo divino",
                },
            ],
            "monsters.json": [
                {
                    "id": "deva",
                    "name": "Deva",
                    "resistances": "fuoco",
                    "condition_immunities": "avvelenato",
                    "traits": [
                        {
                            "name": "Incantesimi innati",
                            "description": "Il deva lancia Comunione a volontà",
                        },
                    ],
                },
            ],
        }
        cats = build_catalogs(outputs)
        segmentize_outputs(outputs, cats)

        # Monster trait should reference the spell
        trait = outputs["monsters.json"][0]["traits"][0]
        assert isinstance(trait["description"], list)
        spell_refs = [s for s in trait["description"] if s.get("type") == "spell"]
        assert len(spell_refs) == 1
        assert spell_refs[0]["id"] == "comunione"

        # Monster resistances should reference damage type
        res = outputs["monsters.json"][0]["resistances"]
        assert isinstance(res, list)
        assert any(s["type"] == "damage_type" for s in res)

    def test_empty_string_fields_become_empty_list(self):
        outputs: dict[str, list] = {
            "monsters.json": [
                {
                    "id": "goblin",
                    "name": "Goblin",
                    "resistances": "",
                    "description": "",
                },
            ],
        }
        cats = build_catalogs(outputs)
        segmentize_outputs(outputs, cats)
        assert outputs["monsters.json"][0]["resistances"] == []
        assert outputs["monsters.json"][0]["description"] == []
