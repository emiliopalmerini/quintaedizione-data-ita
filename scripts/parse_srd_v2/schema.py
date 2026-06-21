"""Schema v2 envelope helpers."""

from __future__ import annotations

from typing import Any

from .collections import get_collection
from .manifest import GeneratedMetadata, SourceMetadata, to_jsonable


SCHEMA_VERSION = "2.0.0"


def empty_envelope(
    collection_id: str,
    *,
    source: SourceMetadata,
    generated: GeneratedMetadata,
) -> dict[str, Any]:
    """Build an empty but valid v2 collection envelope."""

    get_collection(collection_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "id": source.id,
            "title": source.title,
            "checksum_sha256": source.checksum_sha256,
            "page_count": source.page_count,
        },
        "generated": to_jsonable(generated),
        "collection": collection_id,
        "items": [],
    }


def validate_envelope(envelope: dict[str, Any]) -> list[str]:
    """Return validation errors for a v2 envelope."""

    errors: list[str] = []
    if envelope.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 2.0.0")

    collection = envelope.get("collection")
    if not isinstance(collection, str):
        errors.append("collection must be a string")
    else:
        try:
            get_collection(collection)
        except KeyError:
            errors.append(f"unknown collection: {collection}")

    source = envelope.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
    else:
        for field in ("id", "title", "checksum_sha256", "page_count"):
            if field not in source:
                errors.append(f"source.{field} is required")

    generated = envelope.get("generated")
    if not isinstance(generated, dict):
        errors.append("generated must be an object")
    else:
        for field in ("parser", "parser_version", "generated_at"):
            if field not in generated:
                errors.append(f"generated.{field} is required")

    items = envelope.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list")
    else:
        seen_ids: set[str] = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"items[{index}] must be an object")
                continue
            entity_id = item.get("id")
            if not isinstance(entity_id, str) or not entity_id:
                errors.append(f"items[{index}].id is required")
            elif entity_id in seen_ids:
                errors.append(f"duplicate item id: {entity_id}")
            else:
                seen_ids.add(entity_id)
            if "source_id" not in item:
                errors.append(f"items[{index}].source_id is required")
            if "provenance" not in item:
                errors.append(f"items[{index}].provenance is required")

    return errors
