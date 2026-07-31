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
            {"page_number": 93, "nodes": [{"text": "Accolito", "page_number": 93}]},
            {"page_number": 118, "nodes": [{"text": "Aiuto", "page_number": 118}]},
        ],
    }

    artifact = assign_sections(document)
    by_id = {section["id"]: section for section in artifact["sections"]}

    assert by_id["origini"]["coverage"] == "covered"
    assert by_id["origini"]["node_count"] == 1
    assert by_id["specie"]["coverage"] == "covered"
    assert by_id["incantesimi"]["node_count"] == 1
    assert by_id["mostri"]["coverage"] == "empty"


def test_assign_sections_splits_shared_origini_specie_pages() -> None:
    document = {
        "source": {"id": "srd-5.2.1-it"},
        "pages": [
            {
                "page_number": 93,
                "nodes": [
                    {"text": "Background dei personaggi", "type": "heading", "page_number": 93},
                    {"text": "Accolito", "type": "heading", "page_number": 93},
                    {"text": "Punteggi di caratteristica: Saggezza", "type": "paragraph", "page_number": 93},
                    {"text": "Specie dei personaggi", "type": "heading", "page_number": 93},
                    {"text": "Dragonide", "type": "heading", "page_number": 94},
                ],
            }
        ],
    }

    artifact = assign_sections(document)
    by_id = {section["id"]: section for section in artifact["sections"]}

    assert [node["text"] for node in by_id["origini"]["nodes"]] == [
        "Background dei personaggi",
        "Accolito",
        "Punteggi di caratteristica: Saggezza",
    ]
    assert [node["text"] for node in by_id["specie"]["nodes"]] == [
        "Specie dei personaggi",
        "Dragonide",
    ]
