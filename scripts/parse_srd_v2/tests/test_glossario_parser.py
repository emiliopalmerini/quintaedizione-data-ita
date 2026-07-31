from __future__ import annotations

from scripts.parse_srd_v2.parsers.glossario_delle_regole import parse_glossario


def test_parse_glossary_entries_and_resolve_related_entries() -> None:
    section = {
        "id": "glossario_delle_regole",
        "page_start": 202,
        "page_end": 219,
        "nodes": [
            {"id": "n1", "type": "heading", "heading_level": 1, "text": "Glossario delle regole", "page_number": 202},
            {"id": "n2", "type": "heading", "heading_level": 2, "text": "Definizione delle regole", "page_number": 202},
            {"id": "n3", "type": "heading", "heading_level": 5, "text": "Accecato [condizione]", "page_number": 202, "heading_path": ["Glossario delle regole", "Definizione delle regole", "Accecato [condizione]"]},
            {"id": "n4", "type": "paragraph", "text": "Il personaggio non vede. Vedi anche \"Condizione\".", "page_number": 202},
            {"id": "n5", "type": "heading", "heading_level": 5, "text": "Condizione", "page_number": 206, "heading_path": ["Glossario delle regole", "Definizione delle regole", "Condizione"]},
            {"id": "n6", "type": "paragraph", "text": "Uno stato temporaneo.", "page_number": 206},
            {"id": "n7", "type": "heading", "heading_level": 5, "text": "Competenza", "page_number": 206, "heading_path": ["Glossario delle regole", "Definizione delle regole", "Competenza"]},
            {"id": "n8", "type": "paragraph", "text": "Una capacità. Vedi anche \"Come si gioca\" (\"Condizione\").", "page_number": 206},
        ],
    }

    result = parse_glossario(section, "srd-5.2.1-it")

    assert [item["id"] for item in result.items] == [
        "accecato-condizione",
        "condizione",
        "competenza",
    ]
    assert result.items[0]["descriptor_id"] == "condizione"
    assert result.items[0]["related_entry_refs"] == [
        {
            "source_id": "srd-5.2.1-it",
            "collection": "glossario_delle_regole",
            "id": "condizione",
            "text": "Condizione",
        }
    ]
    assert result.items[1]["descriptor_id"] is None
    assert result.items[2]["related_entry_refs"] == []
    assert result.ignored_nodes == [
        {"node_id": "n1", "reason": "section_preamble"},
        {"node_id": "n2", "reason": "section_preamble"},
    ]
