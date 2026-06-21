from __future__ import annotations

from scripts.parse_srd_v2.sections import assign_sections, section_ids


def test_section_ids_are_srd_521_ordered() -> None:
    assert section_ids()[:5] == [
        "come_si_gioca",
        "creazione_del_personaggio",
        "classi",
        "origini",
        "specie",
    ]
    assert section_ids()[-2:] == ["mostri", "animali"]


def test_assign_sections_uses_page_ranges() -> None:
    document = {
        "source": {"id": "srd-5.2.1-it"},
        "pages": [
            {"page_number": 93, "paragraphs": [{"text": "Accolito", "page_number": 93}]},
            {"page_number": 118, "paragraphs": [{"text": "Aiuto", "page_number": 118}]},
        ],
    }

    artifact = assign_sections(document)
    by_id = {section["id"]: section for section in artifact["sections"]}

    assert by_id["origini"]["coverage"] == "covered"
    assert by_id["origini"]["paragraph_count"] == 1
    assert by_id["specie"]["coverage"] == "covered"
    assert by_id["incantesimi"]["paragraph_count"] == 1
    assert by_id["mostri"]["coverage"] == "empty"


def test_assign_sections_splits_shared_origini_specie_pages() -> None:
    document = {
        "source": {"id": "srd-5.2.1-it"},
        "pages": [
            {
                "page_number": 93,
                "paragraphs": [
                    {"text": "Background dei personaggi", "role": "heading", "page_number": 93},
                    {"text": "Accolito", "role": "heading", "page_number": 93},
                    {"text": "Punteggi di caratteristica: Saggezza", "role": "body", "page_number": 93},
                    {"text": "Specie dei personaggi", "role": "heading", "page_number": 93},
                    {"text": "Dragonide", "role": "heading", "page_number": 94},
                ],
            }
        ],
    }

    artifact = assign_sections(document)
    by_id = {section["id"]: section for section in artifact["sections"]}

    assert [p["text"] for p in by_id["origini"]["paragraphs"]] == [
        "Background dei personaggi",
        "Accolito",
        "Punteggi di caratteristica: Saggezza",
    ]
    assert [p["text"] for p in by_id["specie"]["paragraphs"]] == [
        "Specie dei personaggi",
        "Dragonide",
    ]
