"""Schema v2 envelope helpers."""

from __future__ import annotations

import re
from typing import Any

from .collections import get_collection
from .manifest import GeneratedMetadata, SourceMetadata, to_jsonable


SCHEMA_VERSION = "2.0.0"

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ENVELOPE_FIELDS = {"schema_version", "source", "generated", "collection", "items"}
_SOURCE_FIELDS = {"id", "title", "checksum_sha256", "page_count"}
_GENERATED_FIELDS = {"parser", "parser_version"}
_PROVENANCE_REQUIRED_FIELDS = {
    "page_start",
    "page_end",
    "heading_path",
    "section_id",
    "parser",
}
_PROVENANCE_FIELDS = _PROVENANCE_REQUIRED_FIELDS | {"bbox_page", "bbox"}
_COMMON_ENTITY_FIELDS = {"id", "name", "source_id", "provenance"}
_ENTITY_FIELDS = {
    "origini": _COMMON_ENTITY_FIELDS
    | {
        "ability_scores",
        "feat",
        "skill_proficiencies",
        "tool_proficiency",
        "equipment",
        "description",
    },
    "specie": _COMMON_ENTITY_FIELDS
    | {"creature_type", "size", "speed", "description", "traits"},
    "talenti": _COMMON_ENTITY_FIELDS
    | {"category", "prerequisite", "repeatable", "benefit"},
}
_STRING_FIELDS = {
    "origini": {
        "ability_scores",
        "feat",
        "skill_proficiencies",
        "tool_proficiency",
        "equipment",
    },
    "specie": {"creature_type", "size", "speed"},
    "talenti": {"category"},
}
_CONTENT_FIELDS = {
    "origini": {"description"},
    "specie": {"description"},
    "talenti": {"benefit"},
}


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
    unknown_envelope_fields = sorted(set(envelope) - _ENVELOPE_FIELDS)
    if unknown_envelope_fields:
        errors.append(
            f"envelope has unknown fields: {', '.join(unknown_envelope_fields)}"
        )
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
        unknown_source_fields = sorted(set(source) - _SOURCE_FIELDS)
        if unknown_source_fields:
            errors.append(f"source has unknown fields: {', '.join(unknown_source_fields)}")
        for field in sorted(_SOURCE_FIELDS):
            if field not in source:
                errors.append(f"source.{field} is required")

    generated = envelope.get("generated")
    if not isinstance(generated, dict):
        errors.append("generated must be an object")
    else:
        unknown_generated_fields = sorted(set(generated) - _GENERATED_FIELDS)
        if unknown_generated_fields:
            errors.append(
                f"generated has unknown fields: {', '.join(unknown_generated_fields)}"
            )
        for field in sorted(_GENERATED_FIELDS):
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
            elif _SLUG.fullmatch(entity_id) is None:
                errors.append(f"items[{index}].id must be a lowercase ASCII slug")
            elif entity_id in seen_ids:
                errors.append(f"duplicate item id: {entity_id}")
            else:
                seen_ids.add(entity_id)

            if not isinstance(item.get("name"), str) or not item.get("name"):
                errors.append(f"items[{index}].name is required")

            source_id = item.get("source_id")
            if not isinstance(source_id, str) or not source_id:
                errors.append(f"items[{index}].source_id is required")
            elif isinstance(source, dict) and source_id != source.get("id"):
                errors.append(f"items[{index}].source_id must match source.id")

            _validate_provenance(item.get("provenance"), index, errors)

            if isinstance(collection, str):
                allowed_fields = _ENTITY_FIELDS.get(collection)
                if allowed_fields is None:
                    errors.append(
                        f"items[{index}] cannot be validated: no schema for {collection}"
                    )
                else:
                    unknown_item_fields = sorted(set(item) - allowed_fields)
                    if unknown_item_fields:
                        errors.append(
                            f"items[{index}] has unknown fields: "
                            f"{', '.join(unknown_item_fields)}"
                        )
                    for field in sorted(allowed_fields - _COMMON_ENTITY_FIELDS):
                        if field not in item:
                            errors.append(f"items[{index}].{field} is required")
                    _validate_entity_fields(collection, item, index, errors)

    return errors


def _validate_provenance(value: Any, index: int, errors: list[str]) -> None:
    prefix = f"items[{index}].provenance"
    if not isinstance(value, dict):
        errors.append(f"{prefix} is required")
        return

    unknown_fields = sorted(set(value) - _PROVENANCE_FIELDS)
    if unknown_fields:
        errors.append(f"{prefix} has unknown fields: {', '.join(unknown_fields)}")
    for field in sorted(_PROVENANCE_REQUIRED_FIELDS):
        if field not in value:
            errors.append(f"{prefix}.{field} is required")

    for field in ("page_start", "page_end"):
        if field in value and not isinstance(value[field], int):
            errors.append(f"{prefix}.{field} must be an integer")
    heading_path = value.get("heading_path")
    if "heading_path" in value and (
        not isinstance(heading_path, list)
        or not heading_path
        or not all(isinstance(part, str) and part for part in heading_path)
    ):
        errors.append(f"{prefix}.heading_path must be a non-empty string list")
    for field in ("section_id", "parser"):
        if field in value and (
            not isinstance(value[field], str) or not value[field]
        ):
            errors.append(f"{prefix}.{field} must be a non-empty string")


def _validate_entity_fields(
    collection: str,
    item: dict[str, Any],
    index: int,
    errors: list[str],
) -> None:
    for field in sorted(_STRING_FIELDS.get(collection, set())):
        if field in item and (
            not isinstance(item[field], str) or not item[field].strip()
        ):
            errors.append(f"items[{index}].{field} must be a non-empty string")

    if collection == "talenti":
        prerequisite = item.get("prerequisite")
        if "prerequisite" in item and not isinstance(prerequisite, str):
            errors.append(f"items[{index}].prerequisite must be a string")
        if "repeatable" in item and not isinstance(item["repeatable"], bool):
            errors.append(f"items[{index}].repeatable must be a boolean")

    for field in sorted(_CONTENT_FIELDS.get(collection, set())):
        if field in item:
            _validate_content(item[field], f"items[{index}].{field}", errors)

    if collection == "specie" and "traits" in item:
        traits = item["traits"]
        if not isinstance(traits, list):
            errors.append(f"items[{index}].traits must be a list")
        else:
            for trait_index, trait in enumerate(traits):
                prefix = f"items[{index}].traits[{trait_index}]"
                if not isinstance(trait, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                unknown = sorted(set(trait) - {"name", "description"})
                if unknown:
                    errors.append(f"{prefix} has unknown fields: {', '.join(unknown)}")
                if not isinstance(trait.get("name"), str) or not trait.get("name"):
                    errors.append(f"{prefix}.name is required")
                _validate_content(trait.get("description"), f"{prefix}.description", errors)


def _validate_content(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{prefix} must be a content segment list")
        return
    for segment_index, segment in enumerate(value):
        segment_prefix = f"{prefix}[{segment_index}]"
        if not isinstance(segment, dict):
            errors.append(f"{segment_prefix} must be an object")
            continue
        segment_type = segment.get("type")
        if not isinstance(segment_type, str) or not segment_type:
            errors.append(f"{segment_prefix}.type is required")
        if not isinstance(segment.get("text"), str) or not segment.get("text"):
            errors.append(f"{segment_prefix}.text is required")
        allowed = {"type", "text"} if segment_type == "text" else {"type", "id", "text"}
        unknown = sorted(set(segment) - allowed)
        if unknown:
            errors.append(f"{segment_prefix} has unknown fields: {', '.join(unknown)}")
        if segment_type != "text" and (
            not isinstance(segment.get("id"), str)
            or _SLUG.fullmatch(segment["id"]) is None
        ):
            errors.append(f"{segment_prefix}.id must be a lowercase ASCII slug")
