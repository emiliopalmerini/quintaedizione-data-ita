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
                "heading_path": [
                    "Equipaggiamento",
                    "Armi",
                    "Armi da mischia semplici",
                    "Randello",
                ],
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
            "attributes": [],
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
    assert result.items[2]["property_ids"] == ["versatile"]
    assert result.items[2]["attributes"] == [
        {
            "id": "proprieta-versatile",
            "name": "Proprietà: Versatile",
            "value": "1d10",
        }
    ]


def test_parse_heading_based_tool_and_service() -> None:
    section = {
        "id": "equipaggiamento",
        "page_start": 101,
        "page_end": 117,
        "nodes": [
            {
                "id": "n1",
                "type": "heading",
                "heading_level": 5,
                "text": "Scorte da alchimista (50 mo)",
                "page_number": 105,
                "heading_path": [
                    "Equipaggiamento",
                    "Strumenti",
                    "Strumenti da artigiano",
                    "Scorte da alchimista (50 mo)",
                ],
            },
            {"id": "n2", "type": "paragraph", "text": "Caratteristica: Intelligenza", "page_number": 105},
            {"id": "n3", "type": "paragraph", "text": "Peso: 4 kg", "page_number": 105},
            {"id": "n4", "type": "paragraph", "text": "Utilizzo: identificare una sostanza (CD 15)", "page_number": 105},
            {
                "id": "n5",
                "type": "heading",
                "heading_level": 4,
                "text": "Miserabile (gratis)",
                "page_number": 114,
                "heading_path": ["Equipaggiamento", "Spese dello stile di vita", "Miserabile (gratis)"],
            },
            {"id": "n6", "type": "paragraph", "text": "Il personaggio vive in condizioni disumane.", "page_number": 114},
        ],
    }

    result = parse_equipaggiamento(section, "srd-5.2.1-it")

    tool, service = result.items
    assert tool["id"] == "scorte-da-alchimista"
    assert tool["name"] == "Scorte da alchimista"
    assert tool["category_id"] == "strumento"
    assert tool["cost"] == {"quantity": 50, "unit": "mo"}
    assert tool["weight"] == {"quantity": 4, "unit": "kg"}
    assert tool["attributes"][0] == {
        "id": "caratteristica",
        "name": "Caratteristica",
        "value": "Intelligenza",
    }
    assert service["category_id"] == "servizio"
    assert service["cost"] == {"quantity": 0, "unit": "mo"}


def test_parse_collapsed_armor_table() -> None:
    section = {
        "id": "equipaggiamento",
        "page_start": 101,
        "page_end": 117,
        "nodes": [
            {
                "id": "n1",
                "type": "table",
                "page_number": 104,
                "heading_path": ["Equipaggiamento", "Armature"],
                "rows": [
                    {"cells": [{"text": "Armatura leggera (1 minuto per indossare o togliere)"}, *({"text": ""} for _ in range(5))]},
                    {"cells": [{"text": "Armatura imbottita 11 + modificatore di Des — Svantaggio 4 kg 5 mo"}, *({"text": ""} for _ in range(5))]},
                    {"cells": [{"text": "Armatura di cuoio"}, {"text": "11 + modificatore di Des"}, {"text": "—"}, {"text": "—"}, {"text": "5 kg"}, {"text": "10 mo"}]},
                ],
            }
        ],
    }

    result = parse_equipaggiamento(section, "srd-5.2.1-it")

    assert [item["id"] for item in result.items] == [
        "armatura-imbottita",
        "armatura-di-cuoio",
    ]
    assert result.items[0]["category_id"] == "armatura"
    assert result.items[0]["attributes"] == [
        {"id": "classe-armatura", "name": "Classe Armatura", "value": "11 + modificatore di Des"},
        {"id": "furtivita", "name": "Furtività", "value": "Svantaggio"},
        {"id": "vestizione", "name": "Vestizione", "value": "1 minuto per indossare o togliere"},
    ]


def test_parse_transport_tables_and_spill_row() -> None:
    section = {
        "id": "equipaggiamento",
        "page_start": 101,
        "page_end": 117,
        "nodes": [
            {"id": "n1", "type": "paragraph", "text": "Cavalcature e altri animali", "page_number": 113},
            {
                "id": "n2",
                "type": "table",
                "page_number": 113,
                "rows": [
                    {"cells": [{"text": "Cammello"}, {"text": "225 kg"}, {"text": "50 mo"}]},
                    {"cells": [{"text": "Cavallo da galoppo 240 kg 75 mo"}, {"text": ""}, {"text": ""}]},
                ],
            },
            {"id": "n3", "type": "paragraph", "text": "Pony 112,5 kg 30 mo", "page_number": 113},
            {"id": "n4", "type": "paragraph", "text": "Veicoli aerei e imbarcazioni", "page_number": 114},
            {
                "id": "n5",
                "type": "table",
                "page_number": 114,
                "rows": [
                    {"cells": [{"text": "Barca a remi"}, {"text": "2,25 km/h"}, {"text": "1"}, {"text": "3"}, {"text": "—"}, {"text": "11"}, {"text": "50"}, {"text": "—"}, {"text": "50 mo"}]}
                ],
            },
        ],
    }

    result = parse_equipaggiamento(section, "srd-5.2.1-it")

    assert [item["id"] for item in result.items] == [
        "cammello",
        "cavallo-da-galoppo",
        "pony",
        "barca-a-remi",
    ]
    assert result.items[0]["category_id"] == "cavalcatura"
    assert result.items[0]["attributes"] == [
        {
            "id": "capacita-di-trasporto",
            "name": "Capacità di trasporto",
            "value": "225 kg",
        }
    ]
    assert result.items[-1]["category_id"] == "veicolo"
    assert result.items[-1]["attributes"][0] == {
        "id": "velocita",
        "name": "Velocità",
        "value": "2,25 km/h",
    }
