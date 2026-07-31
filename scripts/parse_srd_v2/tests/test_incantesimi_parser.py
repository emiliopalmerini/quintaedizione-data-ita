from __future__ import annotations

from scripts.parse_srd_v2.parsers.incantesimi import (
    _extract_metadata,
    _metadata_fields,
    parse_incantesimi,
)


def test_extract_all_fields_from_merged_metadata_node() -> None:
    assert _metadata_fields(
        "Tempo di lancio: azione Gittata: 36 metri Componenti: S "
        "Durata: concentrazione, fino a 1 ora"
    ) == {
        "casting_time": "azione",
        "range": "36 metri",
        "components": "S",
        "duration": "concentrazione, fino a 1 ora",
    }


def test_extract_metadata_appends_wrapped_values() -> None:
    fields, remaining = _extract_metadata(
        [
            {"text": "Tempo di lancio: reazione che l'incantatore può"},
            {"text": "effettuare quando una creatura cade"},
            {"text": "Gittata: 18 metri"},
            {"text": "Componenti: V, M (una piccola"},
            {"text": "piuma)"},
            {"text": "Durata: 1 minuto"},
            {"text": "Descrizione dell'incantesimo."},
        ]
    )

    assert fields == {
        "casting_time": "reazione che l'incantatore può effettuare quando una creatura cade",
        "range": "18 metri",
        "components": "V, M (una piccola piuma)",
        "duration": "1 minuto",
    }
    assert remaining == [{"text": "Descrizione dell'incantesimo."}]


def test_parse_structurally_discovered_spell() -> None:
    section = {
        "id": "incantesimi",
        "title": "Incantesimi",
        "page_start": 118,
        "page_end": 201,
        "nodes": [
            {
                "id": "p0140-n0001",
                "type": "heading",
                "heading_level": 2,
                "text": "Descrizioni degli incantesimi",
                "page_number": 140,
                "heading_path": ["Incantesimi", "Descrizioni degli incantesimi"],
            },
            {
                "id": "p0140-n0002",
                "type": "heading",
                "heading_level": 5,
                "text": "Allarme",
                "page_number": 140,
                "heading_path": [
                    "Incantesimi",
                    "Descrizioni degli incantesimi",
                    "Allarme",
                ],
            },
            {
                "id": "p0140-n0003",
                "type": "paragraph",
                "text": "Abiurazione di 1\u00ba livello (Mago, Ranger)",
                "page_number": 140,
            },
            {
                "id": "p0140-n0004",
                "type": "paragraph",
                "text": "Tempo di lancio: 1 minuto o rituale",
                "page_number": 140,
            },
            {
                "id": "p0140-n0005",
                "type": "paragraph",
                "text": "Gittata: 9 metri",
                "page_number": 140,
            },
            {
                "id": "p0140-n0006",
                "type": "paragraph",
                "text": "Componenti: V, S, M (una campanella d'argento)",
                "page_number": 140,
            },
            {
                "id": "p0140-n0007",
                "type": "paragraph",
                "text": "Durata: Concentrazione, fino a 1 ora",
                "page_number": 140,
            },
            {
                "id": "p0140-n0008",
                "type": "paragraph",
                "text": "L'incantatore predispone un allarme.",
                "page_number": 140,
            },
            {
                "id": "p0140-n0009",
                "type": "paragraph",
                "text": (
                    "Utilizzo di uno slot incantesimo di livello superiore. "
                    "La durata aumenta di 1 ora."
                ),
                "page_number": 140,
            },
        ],
    }

    result = parse_incantesimi(section, "srd-5.2.1-it")

    assert result.items == [
        {
            "id": "allarme",
            "name": "Allarme",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 140,
                "page_end": 140,
                "heading_path": [
                    "Incantesimi",
                    "Descrizioni degli incantesimi",
                    "Allarme",
                ],
                "section_id": "incantesimi",
                "parser": "incantesimi",
            },
            "level": 1,
            "school_id": "abiurazione",
            "class_ids": ["mago", "ranger"],
            "casting_time": "1 minuto o rituale",
            "range": "9 metri",
            "components": {
                "verbal": True,
                "somatic": True,
                "material": True,
                "material_text": "una campanella d'argento",
            },
            "duration": "Concentrazione, fino a 1 ora",
            "ritual": True,
            "concentration": True,
            "description": [
                {"type": "text", "text": "L'incantatore predispone un allarme."}
            ],
            "at_higher_levels": [
                {"type": "text", "text": "La durata aumenta di 1 ora."}
            ],
        }
    ]
    assert result.consumed_node_ids == [
        f"p0140-n{index:04d}" for index in range(2, 10)
    ]
    assert result.ignored_nodes == [
        {"node_id": "p0140-n0001", "reason": "section_preamble"}
    ]
