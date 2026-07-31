from __future__ import annotations

from scripts.parse_srd_v2.parsers.specie import parse_specie


def test_parse_specie_extracts_species_entities_and_traits() -> None:
    section = {
        "id": "specie",
        "title": "Specie",
        "page_start": 93,
        "page_end": 97,
        "nodes": [
            {"text": "Specie dei personaggi", "type": "heading", "page_number": 93},
            {"text": "Descrizioni delle specie", "type": "heading", "page_number": 94},
            {"text": "Dragonide", "type": "heading", "page_number": 94},
            {"text": "Tipo di creatura: umanoide", "type": "paragraph", "page_number": 94},
            {
                "text": "Taglia: Media (altezza di circa 150-210 centimetri)",
                "type": "paragraph",
                "page_number": 94,
            },
            {"text": "Velocit\u00e0: 9 metri", "type": "paragraph", "page_number": 94},
            {
                "text": "In quanto dragonide, il personaggio ha i seguenti",
                "type": "paragraph",
                "page_number": 94,
            },
            {"text": "tratti speciali.", "type": "paragraph", "page_number": 94},
            {
                "text": "Discendenza draconica. Il personaggio discende",
                "type": "paragraph",
                "page_number": 94,
            },
            {"text": "da un progenitore draconico.", "type": "paragraph", "page_number": 94},
            {
                "text": "Soffio. Quando il personaggio esegue l'azione di",
                "type": "paragraph",
                "page_number": 94,
            },
            {"text": "Attacco durante il turno.", "type": "paragraph", "page_number": 94},
            {
                "text": "Resistenza ai danni. Il personaggio dispone di",
                "type": "paragraph",
                "page_number": 94,
            },
            {
                "text": "resistenza ai danni del tipo determinato dal tratto",
                "type": "paragraph",
                "page_number": 94,
            },
            {"text": "Discendenza draconica.", "type": "paragraph", "page_number": 94},
        ],
    }

    items = parse_specie(section, "srd-5.2.1-it")

    assert len(items) == 1
    item = items[0]
    assert item["id"] == "dragonide"
    assert item["name"] == "Dragonide"
    assert item["creature_type"] == "umanoide"
    assert item["size"] == "Media (altezza di circa 150-210 centimetri)"
    assert item["speed"] == "9 metri"
    assert item["description"] == [
        {
            "type": "text",
            "text": "In quanto dragonide, il personaggio ha i seguenti tratti speciali.",
        }
    ]
    assert item["traits"] == [
        {
            "name": "Discendenza draconica",
            "description": [
                {
                    "type": "text",
                    "text": "Il personaggio discende da un progenitore draconico.",
                }
            ],
        },
        {
            "name": "Soffio",
            "description": [
                {
                    "type": "text",
                    "text": "Quando il personaggio esegue l'azione di Attacco durante il turno.",
                }
            ],
        },
        {
            "name": "Resistenza ai danni",
            "description": [
                {
                    "type": "text",
                    "text": (
                        "Il personaggio dispone di resistenza ai danni del tipo "
                        "determinato dal tratto Discendenza draconica."
                    ),
                }
            ],
        },
    ]
    assert item["provenance"]["page_start"] == 94
    assert item["provenance"]["page_end"] == 94


def test_parse_specie_handles_multiline_size_and_multiple_species() -> None:
    section = {
        "id": "specie",
        "title": "Specie",
        "page_start": 93,
        "page_end": 97,
        "nodes": [
            {"text": "Tiefling", "type": "heading", "page_number": 96},
            {"text": "Tipo di creatura: umanoide", "type": "paragraph", "page_number": 96},
            {
                "text": "Taglia: Media (altezza di circa 120-210 centimetri)",
                "type": "paragraph",
                "page_number": 96,
            },
            {
                "text": "o\u00a0Piccola (altezza di circa 90-120 centimetri), a tua",
                "type": "paragraph",
                "page_number": 96,
            },
            {"text": "scelta quando scegli la specie", "type": "paragraph", "page_number": 96},
            {"text": "Velocit\u00e0: 9 metri", "type": "paragraph", "page_number": 96},
            {
                "text": "Retaggio immondo. Grazie alla sua discendenza",
                "type": "paragraph",
                "page_number": 96,
            },
            {"text": "Umano", "type": "heading", "page_number": 97},
            {"text": "Tipo di creatura: umanoide", "type": "paragraph", "page_number": 97},
            {
                "text": "Taglia: Media (altezza di circa 120-150centimetri)",
                "type": "paragraph",
                "page_number": 97,
            },
            {"text": "Velocit\u00e0: 9 metri", "type": "paragraph", "page_number": 97},
            {"text": "Versatile. Ottiene un talento Origini.", "type": "paragraph", "page_number": 97},
        ],
    }

    items = parse_specie(section, "srd-5.2.1-it")

    assert [item["id"] for item in items] == ["tiefling", "umano"]
    assert items[0]["size"] == (
        "Media (altezza di circa 120-210 centimetri) "
        "o Piccola (altezza di circa 90-120 centimetri), a tua scelta quando scegli la specie"
    )
    assert items[0]["traits"][0]["name"] == "Retaggio immondo"
    assert items[1]["size"] == "Media (altezza di circa 120-150 centimetri)"
    assert items[1]["traits"][0]["name"] == "Versatile"
