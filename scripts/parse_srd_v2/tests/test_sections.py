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
