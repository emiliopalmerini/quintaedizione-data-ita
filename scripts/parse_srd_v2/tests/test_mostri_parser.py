from __future__ import annotations

from scripts.parse_srd_v2.parsers.mostri import parse_animali, parse_mostri


def _section(section_id: str = "mostri") -> dict:
    return {
        "id": section_id,
        "title": section_id.title(),
        "page_start": 294,
        "page_end": 384,
        "nodes": [
            {
                "id": "n1",
                "type": "heading",
                "heading_level": 3,
                "text": "Aboleth",
                "page_number": 294,
                "heading_path": ["Mostri A–Z", "Aboleth", "Aboleth"],
            },
            {
                "id": "n2",
                "type": "paragraph",
                "text": "Aberrazione Grande, legale malvagio",
                "page_number": 294,
            },
            {
                "id": "n3",
                "type": "paragraph",
                "text": (
                    "CA 17 Iniziativa +7 (17) PF 150 (20d10 + 40) "
                    "Velocità 3 m, nuoto 12 m"
                ),
                "page_number": 294,
            },
            {
                "id": "n4",
                "type": "table",
                "page_number": 294,
                "rows": [
                    {
                        "cells": [
                            {"text": value}
                            for value in (
                                "For 21", "+5", "+5", "", "Des 9", "−1",
                                "+3", "", "Cos 15", "+2", "+6",
                            )
                        ]
                    },
                    {
                        "cells": [
                            {"text": value}
                            for value in (
                                "Int 18", "+4", "+8", "", "Sag 15", "+2",
                                "+6", "", "Car 18", "+4", "+4",
                            )
                        ]
                    },
                ],
            },
            {
                "id": "n5",
                "type": "paragraph",
                "text": (
                    "Abilità Percezione +10 Sensi Percezione passiva 20 "
                    "Lingue telepatia 36 m GS 10 (PE 5.900; BC +4)"
                ),
                "page_number": 294,
            },
            {
                "id": "n6",
                "type": "heading",
                "heading_level": 6,
                "text": "Tratti",
                "page_number": 294,
            },
            {
                "id": "n7",
                "type": "paragraph",
                "text": "Anfibio. L'aboleth respira in aria e acqua.",
                "page_number": 294,
            },
            {
                "id": "n8",
                "type": "heading",
                "heading_level": 6,
                "text": "Azioni",
                "page_number": 294,
            },
            {
                "id": "n9",
                "type": "paragraph",
                "text": "Tentacolo. Tiro per colpire in mischia: +9.",
                "page_number": 294,
            },
        ],
    }


def test_parse_monster_stat_block() -> None:
    result = parse_mostri(_section(), "srd-5.2.1-it")
    item = result.items[0]
    assert item["id"] == "aboleth"
    assert item["creature_type_id"] == "aberrazione"
    assert item["size_id"] == "grande"
    assert item["ac"] == 17
    assert item["hp"] == {"average": 150, "formula": "20d10 + 40"}
    assert item["ability_scores"] == {
        "for": 21,
        "des": 9,
        "cos": 15,
        "int": 18,
        "sag": 15,
        "car": 18,
    }
    assert item["ability_modifiers"] == {
        "for": 5,
        "des": -1,
        "cos": 2,
        "int": 4,
        "sag": 2,
        "car": 4,
    }
    assert item["saving_throw_bonuses"] == {
        "for": 5,
        "des": 3,
        "cos": 6,
        "int": 8,
        "sag": 6,
        "car": 4,
    }
    assert item["challenge_rating"] == "10"
    assert item["experience_points"] == 5900
    assert item["lair_experience_points"] is None
    assert item["proficiency_bonus"] == 4
    assert item["vulnerabilities"] == ""
    assert item["resistances"] == ""
    assert item["immunities"] == ""
    assert item["equipment"] == ""
    assert item["classification_details"] == ""
    assert item["alternate_size_id"] is None
    assert item["group"] == "Mostri A–Z"
    assert item["provenance"]["heading_path"] == ["Mostri A–Z", "Aboleth"]
    assert item["traits"][0]["name"] == "Anfibio"
    assert item["actions"][0]["name"] == "Tentacolo"
    assert result.ignored_nodes == []


def test_animals_use_separate_collection_parser() -> None:
    result = parse_animali(_section("animali"), "srd-5.2.1-it")
    assert result.items[0]["collection_id"] == "animali"


def test_masculine_size_labels_use_canonical_size_ids() -> None:
    section = _section()
    section["nodes"][1]["text"] = "Umanoide Medio, neutrale"

    result = parse_mostri(section, "srd-5.2.1-it")

    assert result.items[0]["size_id"] == "media"


def test_feature_name_stops_at_period_without_following_space() -> None:
    section = _section()
    section["nodes"][-1]["text"] = "Tentacolo.Tiro per colpire in mischia: +9."

    result = parse_mostri(section, "srd-5.2.1-it")

    assert result.items[0]["actions"][0]["name"] == "Tentacolo"


def test_regular_spans_continue_the_previous_feature() -> None:
    section = _section()
    section["nodes"][-1]["spans"] = [{"text": "Tentacolo.", "flags": 16}]
    section["nodes"].append(
        {
            "id": "n10",
            "type": "paragraph",
            "text": "Il bersaglio ripete il tiro salvezza.",
            "page_number": 294,
            "spans": [{"text": "Il bersaglio ripete il tiro salvezza.", "flags": 4}],
        }
    )

    result = parse_mostri(section, "srd-5.2.1-it")

    actions = result.items[0]["actions"]
    assert len(actions) == 1
    assert actions[0]["description"][0]["text"].endswith("ripete il tiro salvezza.")


def test_wrapped_stat_block_metadata_preserves_all_fields() -> None:
    section = _section()
    section["nodes"][1]["text"] = "Umanoide Medio o Piccolo (licantropo), neutrale"
    section["nodes"][4]["text"] = (
        "Abilità Furtività +7 Resistenze freddo, fulmine Immunità veleno; "
        "avvelenato Attrezzatura armatura di pelle, martelli leggeri (3)"
    )
    section["nodes"].insert(
        5,
        {
            "id": "n5b",
            "type": "paragraph",
            "text": (
                "Sensi Percezione passiva 20 Lingue Comune "
                "GS 10 (PE 5.900, o 7.200 nella tana; BC +4)"
            ),
            "page_number": 294,
        },
    )

    item = parse_mostri(section, "srd-5.2.1-it").items[0]

    assert item["skills"] == "Furtività +7"
    assert item["resistances"] == "freddo, fulmine"
    assert item["immunities"] == "veleno; avvelenato"
    assert item["equipment"] == "armatura di pelle, martelli leggeri (3)"
    assert item["senses"] == "Percezione passiva 20"
    assert item["languages"] == "Comune"
    assert item["lair_experience_points"] == 7200
    assert item["classification_details"] == "o Piccolo (licantropo)"
    assert item["alternate_size_id"] == "piccola"
