from __future__ import annotations

from scripts.parse_srd_v2.parsers.talenti import parse_talenti


def test_parse_talenti_extracts_origin_talent_and_repeatable_flag() -> None:
    section = {
        "id": "talenti",
        "title": "Talenti",
        "page_start": 98,
        "page_end": 100,
        "paragraphs": [
            {"text": "Talenti Origini", "role": "heading", "page_number": 98},
            {"text": "Abile", "role": "heading", "page_number": 98},
            {"text": "Talento Origini", "role": "body", "page_number": 98},
            {
                "text": "Il personaggio ottiene competenza in una combina\u00ad",
                "role": "body",
                "page_number": 98,
            },
            {
                "text": "zione di tre abilit\u00e0 o strumenti a scelta.",
                "role": "body",
                "page_number": 98,
            },
            {
                "text": "Ripetibile. Questo talento \u00e8 ottenibile pi\u00f9 di una",
                "role": "body",
                "page_number": 98,
            },
            {"text": "volta.", "role": "body", "page_number": 98},
        ],
    }

    items = parse_talenti(section, "srd-5.2.1-it")

    assert len(items) == 1
    item = items[0]
    assert item["id"] == "abile"
    assert item["name"] == "Abile"
    assert item["category"] == "Origini"
    assert item["prerequisite"] == ""
    assert item["repeatable"] is True
    assert item["benefit"] == [
        {
            "type": "text",
            "text": (
                "Il personaggio ottiene competenza in una combinazione di tre abilità "
                "o strumenti a scelta. Ripetibile. Questo talento è ottenibile più di una volta."
            ),
        }
    ]
    assert item["provenance"]["page_start"] == 98
    assert item["provenance"]["page_end"] == 98


def test_parse_talenti_handles_wrapped_prerequisite_and_multiple_talents() -> None:
    section = {
        "id": "talenti",
        "title": "Talenti",
        "page_start": 98,
        "page_end": 100,
        "paragraphs": [
            {"text": "Lottatore", "role": "heading", "page_number": 98},
            {
                "text": "Talento Generale (prerequisito: 4\u00ba livello o superiore,",
                "role": "body",
                "page_number": 98,
            },
            {"text": "Forza o Destrezza 13 o superiore)", "role": "body", "page_number": 98},
            {"text": "Il personaggio ottiene i seguenti benefici.", "role": "body", "page_number": 98},
            {
                "text": "Incremento dei punteggi di caratteristica. Il suo",
                "role": "body",
                "page_number": 98,
            },
            {"text": "punteggio di Forza aumenta di 1.", "role": "body", "page_number": 98},
            {"text": "Dono del richiamo degli incantesimi", "role": "heading", "page_number": 100},
            {
                "text": "Talento Dono epico (prerequisito: 19\u00ba livello",
                "role": "body",
                "page_number": 100,
            },
            {"text": "o superiore, privilegio Incantesimi)", "role": "body", "page_number": 100},
            {"text": "Il personaggio ottiene i seguenti benefici.", "role": "body", "page_number": 100},
        ],
    }

    items = parse_talenti(section, "srd-5.2.1-it")

    assert [item["id"] for item in items] == [
        "lottatore",
        "dono-del-richiamo-degli-incantesimi",
    ]
    assert items[0]["category"] == "Generale"
    assert items[0]["prerequisite"] == "4º livello o superiore, Forza o Destrezza 13 o superiore"
    assert items[0]["repeatable"] is False
    assert items[0]["benefit"][0]["text"].startswith(
        "Il personaggio ottiene i seguenti benefici. Incremento dei punteggi"
    )
    assert items[1]["category"] == "Dono epico"
    assert items[1]["prerequisite"] == "19º livello o superiore, privilegio Incantesimi"
