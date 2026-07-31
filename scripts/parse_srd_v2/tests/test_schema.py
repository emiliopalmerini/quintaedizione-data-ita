from __future__ import annotations

from scripts.parse_srd_v2.manifest import GeneratedMetadata, SourceMetadata
from scripts.parse_srd_v2.schema import empty_envelope, validate_envelope


def _source() -> SourceMetadata:
    return SourceMetadata(
        id="srd-5.2.1-it",
        title="System Reference Document 5.2.1 Italiano",
        checksum_sha256="abc",
        page_count=405,
        profile="srd-5.2.1-it",
    )


def _generated() -> GeneratedMetadata:
    return GeneratedMetadata(
        parser="parse_srd_v2",
        parser_version="test",
    )


def test_empty_envelope_uses_canonical_collection_id() -> None:
    envelope = empty_envelope("incantesimi", source=_source(), generated=_generated())

    assert envelope["schema_version"] == "2.0.0"
    assert envelope["collection"] == "incantesimi"
    assert envelope["items"] == []
    assert validate_envelope(envelope) == []


def test_validate_envelope_rejects_duplicate_item_ids() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["items"] = [
        {"id": "soldato", "source_id": "srd-5.2.1-it", "provenance": {}},
        {"id": "soldato", "source_id": "srd-5.2.1-it", "provenance": {}},
    ]

    assert "duplicate item id: soldato" in validate_envelope(envelope)


def test_validate_envelope_rejects_unknown_collection() -> None:
    envelope = empty_envelope("incantesimi", source=_source(), generated=_generated())
    envelope["collection"] = "spells"

    assert "unknown collection: spells" in validate_envelope(envelope)


def test_validate_envelope_rejects_incomplete_entity_contract() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "Soldato",
            "source_id": "another-source",
            "provenance": {},
            "unknown": True,
        }
    ]

    errors = validate_envelope(envelope)

    assert "items[0].id must be a lowercase ASCII slug" in errors
    assert "items[0].name is required" in errors
    assert "items[0].source_id must match source.id" in errors
    assert "items[0].provenance.page_start is required" in errors
    assert "items[0].provenance.page_end is required" in errors
    assert "items[0].provenance.heading_path is required" in errors
    assert "items[0].provenance.section_id is required" in errors
    assert "items[0].provenance.parser is required" in errors
    assert "items[0] has unknown fields: unknown" in errors


def test_validate_envelope_rejects_unknown_envelope_fields() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["generated_at"] = "2026-01-01T00:00:00Z"

    assert "envelope has unknown fields: generated_at" in validate_envelope(envelope)


def test_validate_envelope_rejects_invalid_collection_field_types() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "soldato",
            "name": "Soldato",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": "93",
                "page_end": 92,
                "heading_path": [],
                "section_id": "",
                "parser": "origini",
            },
            "ability_scores": [],
            "feat": "Aggressore selvaggio",
            "skill_proficiencies": "Atletica e Intimidire",
            "tool_proficiency": "Strumenti da gioco",
            "equipment": "Lancia e abito comune",
            "description": "testo",
        }
    ]

    errors = validate_envelope(envelope)

    assert "items[0].provenance.page_start must be an integer" in errors
    assert "items[0].provenance.heading_path must be a non-empty string list" in errors
    assert "items[0].provenance.section_id must be a non-empty string" in errors
    assert "items[0].ability_scores must be a non-empty string" in errors
    assert "items[0].description must be a content segment list" in errors


def test_validate_envelope_accepts_typed_weapon_equipment() -> None:
    envelope = empty_envelope(
        "equipaggiamento",
        source=_source(),
        generated=_generated(),
    )
    envelope["items"] = [
        {
            "id": "randello",
            "name": "Randello",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 101,
                "page_end": 101,
                "heading_path": ["Equipaggiamento", "Armi", "Randello"],
                "section_id": "equipaggiamento",
                "parser": "equipaggiamento",
            },
            "category_id": "arma",
            "subcategory_id": "armi-da-mischia-semplici",
            "subcategory_name": "Armi da mischia semplici",
            "cost": {"quantity": 1, "unit": "ma"},
            "weight": {"quantity": 1, "unit": "kg"},
            "damage": {"dice": "1d4", "type_id": "contundenti"},
            "property_ids": ["leggera"],
            "mastery_id": "rallentare",
            "description": [],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["cost"] = {"quantity": "1", "unit": "ma", "extra": True}
    errors = validate_envelope(envelope)
    assert "items[0].cost has unknown fields: extra" in errors
    assert "items[0].cost.quantity must be a number" in errors
