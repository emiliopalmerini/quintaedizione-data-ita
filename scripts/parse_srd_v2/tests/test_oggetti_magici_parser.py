from __future__ import annotations

from scripts.parse_srd_v2.parsers.oggetti_magici import parse_oggetti_magici


def test_parse_magic_item_subtitle_and_attunement() -> None:
    section = {
        "id": "oggetti_magici",
        "title": "Oggetti magici",
        "page_start": 232,
        "page_end": 288,
        "nodes": [
            {
                "id": "p0237-n0001",
                "type": "heading",
                "heading_level": 2,
                "text": "Oggetti magici A–Z",
                "page_number": 237,
                "heading_path": ["Oggetti magici", "Oggetti magici A–Z"],
            },
            {
                "id": "p0237-n0002",
                "type": "heading",
                "heading_level": 5,
                "text": "Amuleto anti-individuazione e localizzazione",
                "page_number": 237,
                "heading_path": [
                    "Oggetti magici",
                    "Oggetti magici A–Z",
                    "Amuleto anti-individuazione e localizzazione",
                ],
            },
            {
                "id": "p0237-n0003",
                "type": "paragraph",
                "text": "Oggetto meraviglioso, non comune (richiede sintonia da un mago)",
                "page_number": 237,
            },
            {
                "id": "p0237-n0004",
                "type": "paragraph",
                "text": "Il personaggio non può essere individuato magicamente.",
                "page_number": 237,
            },
        ],
    }

    result = parse_oggetti_magici(section, "srd-5.2.1-it")

    assert result.items == [
        {
            "id": "amuleto-anti-individuazione-e-localizzazione",
            "name": "Amuleto anti-individuazione e localizzazione",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 237,
                "page_end": 237,
                "heading_path": [
                    "Oggetti magici",
                    "Oggetti magici A–Z",
                    "Amuleto anti-individuazione e localizzazione",
                ],
                "section_id": "oggetti_magici",
                "parser": "oggetti_magici",
            },
            "type_id": "oggetto-meraviglioso",
            "type_name": "Oggetto meraviglioso",
            "rarity_id": "non-comune",
            "attunement": {"required": True, "requirement_text": "da un mago"},
            "description": [
                {
                    "type": "text",
                    "text": "Il personaggio non può essere individuato magicamente.",
                }
            ],
        }
    ]
    assert result.consumed_node_ids == [
        "p0237-n0002",
        "p0237-n0003",
        "p0237-n0004",
    ]
    assert result.ignored_nodes == [
        {"node_id": "p0237-n0001", "reason": "section_preamble"}
    ]
