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


def test_parse_origini_stops_at_species_boundary() -> None:
    section = {
        "id": "origini",
        "title": "Origini",
        "page_start": 93,
        "page_end": 97,
        "paragraphs": [
            {"text": "Soldato", "role": "heading", "page_number": 93},
            {"text": "Punteggi di caratteristica: Forza, Destrezza,", "role": "body", "page_number": 93},
            {"text": "Costituzione", "role": "body", "page_number": 93},
            {"text": "Talento: Aggressore selvaggio", "role": "body", "page_number": 93},
            {"text": "Competenze nelle abilit\u00e0: Atletica e Intimidire", "role": "body", "page_number": 93},
            {"text": "Competenza negli strumenti: Un tipo di gioco a scelta", "role": "body", "page_number": 93},
            {"text": "(vedi \"Equipaggiamento\")", "role": "body", "page_number": 93},
            {"text": "Equipaggiamento:a scelta tra A e B: (A) lancia, arco", "role": "body", "page_number": 93},
            {"text": "corto, 20 frecce", "role": "body", "page_number": 93},
            {"text": "Specie dei personaggi", "role": "heading", "page_number": 93},
            {"text": "Dragonide", "role": "heading", "page_number": 94},
        ],
    }

    items = parse_origini(section, "srd-5.2.1-it")

    assert len(items) == 1
    item = items[0]
    assert item["ability_scores"] == "Forza, Destrezza, Costituzione"
    assert item["tool_proficiency"] == "Un tipo di gioco a scelta (vedi \"Equipaggiamento\")"
    assert item["equipment"] == "a scelta tra A e B: (A) lancia, arco corto, 20 frecce"
    assert item["description"] == []
