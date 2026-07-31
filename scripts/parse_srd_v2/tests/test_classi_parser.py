from __future__ import annotations

from scripts.parse_srd_v2.parsers.classi import (
    _parse_progression,
    _parse_subclasses,
    _progression_headers,
    _spell_list_names,
    parse_classi,
)


def test_parse_progression_without_header_and_with_collapsed_row() -> None:
    table = {
        "rows": [
            {
                "cells": [
                    {"text": "1"},
                    {"text": "+2"},
                    {"text": "Ira"},
                    {"text": "2"},
                    {"text": "+2"},
                    {"text": "2"},
                ]
            },
            {
                "cells": [
                    {"text": "2 +2 Attacco irruento, Percezione del pericolo 2 +2 2"},
                    {"text": ""},
                    {"text": ""},
                    {"text": ""},
                    {"text": ""},
                    {"text": ""},
                ]
            },
            {
                "cells": [
                    {"text": "3"},
                    {"text": "+2"},
                    {"text": "—"},
                    {"text": "3"},
                    {"text": "+2"},
                    {"text": "2"},
                ]
            },
        ]
    }

    progression, levels = _parse_progression(table, "barbaro")

    assert [row["level"] for row in progression] == [1, 2, 3]
    assert progression[1]["feature_ids"] == [
        "barbaro-attacco-irruento",
        "barbaro-percezione-del-pericolo",
    ]
    assert progression[1]["resources"] == [
        {"id": "resource-1", "value": "2"},
        {"id": "resource-2", "value": "+2"},
        {"id": "resource-3", "value": "2"},
    ]
    assert progression[2]["feature_ids"] == []
    assert levels["attacco-irruento"] == 2


def test_parse_class_with_progression_and_feature() -> None:
    section = {
        "id": "classi",
        "title": "Classi",
        "page_start": 32,
        "page_end": 92,
        "nodes": [
            {
                "id": "p0032-n0001",
                "type": "heading",
                "heading_level": 1,
                "text": "Classi",
                "page_number": 32,
                "heading_path": ["Classi"],
            },
            {
                "id": "p0033-n0001",
                "type": "heading",
                "heading_level": 2,
                "text": "Barbaro",
                "page_number": 33,
                "heading_path": ["Classi", "Barbaro"],
            },
            {
                "id": "p0033-n0002",
                "type": "paragraph",
                "text": "Dado vita: d12",
                "page_number": 33,
            },
            {
                "id": "p0034-n0001",
                "type": "table",
                "page_number": 34,
                "heading_path": ["Classi", "Barbaro"],
                "rows": [
                    {
                        "cells": [
                            {"text": "Livello"},
                            {"text": "Bonus di competenza"},
                            {"text": "Privilegi"},
                            {"text": "Ira"},
                            {"text": "Danni dell'ira"},
                        ]
                    },
                    {
                        "cells": [
                            {"text": "1"},
                            {"text": "+2"},
                            {"text": "Ira"},
                            {"text": "2"},
                            {"text": "+2"},
                        ]
                    },
                    {
                        "cells": [
                            {"text": "2"},
                            {"text": "+2"},
                            {"text": "Attacco irruento"},
                            {"text": "2"},
                            {"text": "+2"},
                        ]
                    },
                ],
            },
            {
                "id": "p0035-n0001",
                "type": "heading",
                "heading_level": 5,
                "text": "Ira",
                "page_number": 35,
                "heading_path": ["Classi", "Barbaro", "Ira"],
            },
            {
                "id": "p0035-n0002",
                "type": "paragraph",
                "text": "Il barbaro combatte con furia primordiale.",
                "page_number": 35,
            },
        ],
    }

    result = parse_classi(section, "srd-5.2.1-it")

    assert len(result.items) == 1
    item = result.items[0]
    assert item["id"] == "barbaro"
    assert item["hit_die"] == 12
    assert item["progression"] == [
        {
            "level": 1,
            "proficiency_bonus": 2,
            "feature_ids": ["barbaro-ira"],
            "resources": [
                {"id": "ira", "value": "2"},
                {"id": "danni-dell-ira", "value": "+2"},
            ],
        },
        {
            "level": 2,
            "proficiency_bonus": 2,
            "feature_ids": ["barbaro-attacco-irruento"],
            "resources": [
                {"id": "ira", "value": "2"},
                {"id": "danni-dell-ira", "value": "+2"},
            ],
        },
    ]
    assert item["features"] == [
        {
            "id": "barbaro-ira",
            "name": "Ira",
            "level": 1,
            "provenance": {
                "page_start": 35,
                "page_end": 35,
                "heading_path": ["Classi", "Barbaro", "Ira"],
                "section_id": "classi",
                "parser": "classi",
            },
            "description": [
                {
                    "type": "text",
                    "text": "Il barbaro combatte con furia primordiale.",
                }
            ],
        }
    ]
    assert item["subclasses"] == []
    assert item["spell_ids"] == []
    assert item["description"] == []
    assert result.consumed_node_ids == [
        "p0033-n0001",
        "p0033-n0002",
        "p0034-n0001",
        "p0035-n0001",
        "p0035-n0002",
    ]
    assert result.ignored_nodes == [
        {"node_id": "p0032-n0001", "reason": "section_preamble"}
    ]


def test_progression_headers_follow_table_column_geometry() -> None:
    nodes = [
        {
            "type": "paragraph",
            "page_number": 32,
            "spans": [
                {"text": "Livello", "bbox": [65, 406, 96, 417]},
                {"text": "Ire", "bbox": [399, 406, 411, 417]},
                {"text": "Danni dell'ira", "bbox": [442, 395, 471, 417]},
            ],
        },
        {
            "type": "table",
            "page_number": 32,
            "bbox": [63, 418, 540, 706],
            "rows": [
                {
                    "cells": [
                        {"text": "1", "bbox": [63, 418, 101, 433]},
                        {"text": "+2", "bbox": [101, 418, 166, 433]},
                        {"text": "Ira", "bbox": [166, 418, 380, 433]},
                        {"text": "2", "bbox": [380, 418, 429, 433]},
                        {"text": "+2", "bbox": [429, 418, 483, 433]},
                    ]
                }
            ],
        },
    ]

    assert _progression_headers(nodes, 1) == [
        "Livello",
        "Bonus di competenza",
        "Privilegi",
        "Ire",
        "Danni dell'ira",
    ]


def test_parse_both_subclass_heading_forms() -> None:
    nodes = [
        {"type": "heading", "heading_level": 4, "text": "Sottoclasse del barbaro:", "page_number": 34},
        {"type": "heading", "heading_level": 4, "text": "Cammino del berserker", "page_number": 34},
        {"type": "heading", "heading_level": 5, "text": "Livello 3: Frenesia", "page_number": 34},
        {"type": "paragraph", "text": "Il barbaro entra in frenesia.", "page_number": 34},
    ]

    subclasses = _parse_subclasses(nodes, "barbaro", {"id": "classi"})

    assert subclasses[0]["id"] == "barbaro-cammino-del-berserker"
    assert subclasses[0]["features"][0]["id"] == (
        "barbaro-cammino-del-berserker-frenesia"
    )
    assert subclasses[0]["features"][0]["level"] == 3

    inline = [
        {"type": "heading", "heading_level": 4, "text": "Sottoclasse del chierico: Dominio della Vita", "page_number": 45},
        {"type": "heading", "heading_level": 5, "text": "Livello 3: Preservare vita", "page_number": 45},
    ]
    assert _parse_subclasses(inline, "chierico", {"id": "classi"})[0]["name"] == (
        "Dominio della Vita"
    )


def test_parse_spell_list_rows_with_interleaved_school_text() -> None:
    nodes = [
        {
            "type": "table",
            "heading_path": ["Classi", "Mago", "Lista degli incantesimi da mago"],
            "rows": [
                {
                    "cells": [
                        {"text": "Protezione dal bene e dal Abiurazione C, M\nmale"},
                        {"text": ""},
                        {"text": ""},
                    ]
                },
                {
                    "cells": [
                        {"text": "Allarme"},
                        {"text": "Abiurazione"},
                        {"text": "R"},
                    ]
                },
            ],
        }
    ]

    assert _spell_list_names(nodes) == ["Protezione dal bene e dal male", "Allarme"]
