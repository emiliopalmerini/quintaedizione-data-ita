from __future__ import annotations

from scripts.parse_srd_v2.parsers.equipaggiamento import parse_equipaggiamento


def test_parse_weapon_table_into_typed_equipment() -> None:
    section = {
        "id": "equipaggiamento",
        "title": "Equipaggiamento",
        "page_start": 101,
        "page_end": 117,
        "nodes": [
            {
                "id": "p0101-n0001",
                "type": "heading",
                "text": "Armi",
                "page_number": 101,
                "heading_path": ["Equipaggiamento", "Armi"],
            },
            {
                "id": "p0101-n0002",
                "type": "table",
                "page_number": 101,
                "bbox": [20.0, 100.0, 580.0, 180.0],
                "heading_path": ["Equipaggiamento", "Armi"],
                "rows": [
                    {
                        "cells": [
                            {"text": "Nome", "bbox": []},
                            {"text": "Costo", "bbox": []},
                            {"text": "Danni", "bbox": []},
                            {"text": "Peso", "bbox": []},
                            {"text": "Propriet\u00e0", "bbox": []},
                            {"text": "Padronanza", "bbox": []},
                        ]
                    },
                    {
                        "cells": [
                            {"text": "Armi da mischia semplici", "bbox": []},
                            {"text": "", "bbox": []},
                            {"text": "", "bbox": []},
                            {"text": "", "bbox": []},
                            {"text": "", "bbox": []},
                            {"text": "", "bbox": []},
                        ]
                    },
                    {
                        "cells": [
                            {"text": "Randello", "bbox": []},
                            {"text": "1 MA", "bbox": []},
                            {"text": "1d4 contundenti", "bbox": []},
                            {"text": "1 kg", "bbox": []},
                            {"text": "Leggera", "bbox": []},
                            {"text": "Rallentare", "bbox": []},
                        ]
                    },
                ],
            },
        ],
    }

    result = parse_equipaggiamento(section, "srd-5.2.1-it")

    assert result.items == [
        {
            "id": "randello",
            "name": "Randello",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 101,
                "page_end": 101,
                "heading_path": ["Equipaggiamento", "Armi", "Randello"],
                "section_id": "equipaggiamento",
                "parser": "equipaggiamento",
            },
            "category_id": "arma",
            "subcategory_id": "armi-da-mischia-semplici",
            "subcategory_name": "Armi da mischia semplici",
            "cost": {"quantity": 1, "unit": "ma"},
            "weight": {"quantity": 1, "unit": "kg"},
            "damage": {"dice": "1d4", "type_id": "contundenti"},
            "property_ids": ["leggera"],
            "mastery_id": "rallentare",
            "description": [],
        }
    ]
    assert result.consumed_node_ids == ["p0101-n0002"]
    assert result.ignored_nodes == [
        {"node_id": "p0101-n0001", "reason": "section_preamble"}
    ]


def test_parse_real_weapon_table_without_header_and_collapsed_rows() -> None:
    section = {
        "id": "equipaggiamento",
        "title": "Equipaggiamento",
        "page_start": 101,
        "page_end": 117,
        "nodes": [
            {
                "id": "p0103-n0008",
                "type": "table",
                "page_number": 103,
                "heading_path": ["Equipaggiamento", "Armi"],
                "rows": [
                    {
                        "cells": [
                            {"text": "Armi da mischia semplici"},
                            {"text": ""},
                            {"text": ""},
                            {"text": ""},
                            {"text": ""},
                            {"text": ""},
                        ]
                    },
                    {
                        "cells": [
                            {"text": "Randello"},
                            {"text": "1d4 contundenti"},
                            {"text": "Leggera"},
                            {"text": "Lentezza"},
                            {"text": "1 kg"},
                            {"text": "1 mo"},
                        ]
                    },
                    {
                        "cells": [
                            {
                                "text": (
                                    "Pugnale 1d4 perforanti Accurata, leggera "
                                    "Vessazione 0,5 kg 2 mo"
                                )
                            },
                            {"text": ""},
                            {"text": ""},
                            {"text": ""},
                            {"text": ""},
                            {"text": ""},
                        ]
                    },
                ],
            },
            {
                "id": "p0103-n0009",
                "type": "paragraph",
                "page_number": 103,
                "heading_path": ["Equipaggiamento", "Armi"],
                "text": (
                    "Spada lunga 1d8 taglienti Versatile (1d10) "
                    "Fiaccare 1,5 kg 15 mo"
                ),
            },
        ],
    }

    result = parse_equipaggiamento(section, "srd-5.2.1-it")

    assert [item["id"] for item in result.items] == [
        "randello",
        "pugnale",
        "spada-lunga",
    ]
    assert result.items[1]["damage"] == {"dice": "1d4", "type_id": "perforanti"}
    assert result.items[1]["property_ids"] == ["accurata", "leggera"]
    assert result.items[1]["mastery_id"] == "vessazione"
    assert result.items[1]["weight"] == {"quantity": 0.5, "unit": "kg"}
    assert result.items[1]["cost"] == {"quantity": 2, "unit": "mo"}
