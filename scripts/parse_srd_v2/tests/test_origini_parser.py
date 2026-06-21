from __future__ import annotations

from scripts.parse_srd_v2.parsers.origini import parse_origini


def test_parse_origini_extracts_origin_entities() -> None:
    section = {
        "id": "origini",
        "title": "Origini",
        "page_start": 93,
        "page_end": 97,
        "paragraphs": [
            {"text": "Origini dei personaggi", "role": "heading", "page_number": 93},
            {"text": "Accolito", "role": "heading", "page_number": 93},
            {
                "text": "Punteggi di caratteristica: Intelligenza, Saggezza, Carisma",
                "role": "body",
                "page_number": 93,
            },
            {"text": "Talento: Iniziato alla Magia", "role": "body", "page_number": 93},
            {
                "text": "Competenze nelle abilit\u00e0: Intuizione e Religione",
                "role": "body",
                "page_number": 93,
            },
            {
                "text": "Competenza negli strumenti: Strumenti da calligrafo",
                "role": "body",
                "page_number": 93,
            },
            {
                "text": "Equipaggiamento: Abito comune, simbolo sacro",
                "role": "body",
                "page_number": 93,
            },
            {
                "text": "Hai trascorso la vita al servizio di un tempio.",
                "role": "body",
                "page_number": 94,
            },
        ],
    }

    items = parse_origini(section, "srd-5.2.1-it")

    assert len(items) == 1
    item = items[0]
    assert item["id"] == "accolito"
    assert item["name"] == "Accolito"
    assert item["source_id"] == "srd-5.2.1-it"
    assert item["ability_scores"] == "Intelligenza, Saggezza, Carisma"
    assert item["feat"] == "Iniziato alla Magia"
    assert item["skill_proficiencies"] == "Intuizione e Religione"
    assert item["tool_proficiency"] == "Strumenti da calligrafo"
    assert item["equipment"] == "Abito comune, simbolo sacro"
    assert item["description"][0]["text"] == "Hai trascorso la vita al servizio di un tempio."
    assert item["provenance"]["page_start"] == 93
    assert item["provenance"]["page_end"] == 94
