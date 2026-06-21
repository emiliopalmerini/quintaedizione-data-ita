from __future__ import annotations

from scripts.parse_srd_v2.manifest import GeneratedMetadata, SourceMetadata
from scripts.parse_srd_v2.schema import empty_envelope, validate_envelope


def _source() -> SourceMetadata:
    return SourceMetadata(
        id="srd-5.2.1-it",
        title="System Reference Document 5.2.1 Italiano",
        path="source.pdf",
        checksum_sha256="abc",
        page_count=405,
        profile="srd-5.2.1-it",
    )


def _generated() -> GeneratedMetadata:
    return GeneratedMetadata(
        parser="parse_srd_v2",
        parser_version="test",
        generated_at="2026-01-01T00:00:00Z",
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
