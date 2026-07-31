from __future__ import annotations

from scripts.parse_srd_v2.parsers.origini import parse_origini


def test_parse_origini_extracts_origin_entities() -> None:
    section = {
        "id": "origini",
        "title": "Origini",
        "page_start": 93,
        "page_end": 97,
        "nodes": [
            {"text": "Origini dei personaggi", "type": "heading", "page_number": 93},
            {"text": "Accolito", "type": "heading", "page_number": 93},
            {
                "text": "Punteggi di caratteristica: Intelligenza, Saggezza, Carisma",
                "type": "paragraph",
                "page_number": 93,
            },
            {"text": "Talento: Iniziato alla Magia", "type": "paragraph", "page_number": 93},
            {
                "text": "Competenze nelle abilit\u00e0: Intuizione e Religione",
                "type": "paragraph",
                "page_number": 93,
            },
            {
                "text": "Competenza negli strumenti: Strumenti da calligrafo",
                "type": "paragraph",
                "page_number": 93,
            },
            {
                "text": "Equipaggiamento: Abito comune, simbolo sacro",
                "type": "paragraph",
                "page_number": 93,
            },
            {
                "text": "Hai trascorso la vita al servizio di un tempio.",
                "type": "paragraph",
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
        "nodes": [
            {"text": "Soldato", "type": "heading", "page_number": 93},
            {"text": "Punteggi di caratteristica: Forza, Destrezza,", "type": "paragraph", "page_number": 93},
            {"text": "Costituzione", "type": "paragraph", "page_number": 93},
            {"text": "Talento: Aggressore selvaggio", "type": "paragraph", "page_number": 93},
            {"text": "Competenze nelle abilit\u00e0: Atletica e Intimidire", "type": "paragraph", "page_number": 93},
            {"text": "Competenza negli strumenti: Un tipo di gioco a scelta", "type": "paragraph", "page_number": 93},
            {"text": "(vedi \"Equipaggiamento\")", "type": "paragraph", "page_number": 93},
            {"text": "Equipaggiamento:a scelta tra A e B: (A) lancia, arco", "type": "paragraph", "page_number": 93},
            {"text": "corto, 20 frecce", "type": "paragraph", "page_number": 93},
            {"text": "Specie dei personaggi", "type": "heading", "page_number": 93},
            {"text": "Dragonide", "type": "heading", "page_number": 94},
        ],
    }

    items = parse_origini(section, "srd-5.2.1-it")

    assert len(items) == 1
    item = items[0]
    assert item["ability_scores"] == "Forza, Destrezza, Costituzione"
    assert item["tool_proficiency"] == "Un tipo di gioco a scelta (vedi \"Equipaggiamento\")"
    assert item["equipment"] == "a scelta tra A e B: (A) lancia, arco corto, 20 frecce"
    assert item["description"] == []
