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
_BASE_ENTITY_FIELDS = {"id", "source_id", "provenance"}
_COMMON_ENTITY_FIELDS = _BASE_ENTITY_FIELDS | {"name"}
_LABEL_FIELDS = {"regole": "title", "glossario_delle_regole": "term"}
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
    "equipaggiamento": _COMMON_ENTITY_FIELDS
    | {
        "category_id",
        "subcategory_id",
        "subcategory_name",
        "cost",
        "weight",
        "damage",
        "property_ids",
        "mastery_id",
        "description",
    },
    "incantesimi": _COMMON_ENTITY_FIELDS
    | {
        "level",
        "school_id",
        "class_ids",
        "casting_time",
        "range",
        "components",
        "duration",
        "ritual",
        "concentration",
        "description",
        "at_higher_levels",
    },
    "classi": _COMMON_ENTITY_FIELDS
    | {
        "hit_die",
        "progression",
        "features",
        "subclasses",
        "spell_ids",
        "description",
    },
    "regole": _BASE_ENTITY_FIELDS
    | {"title", "parent_id", "depth", "order", "content"},
    "oggetti_magici": _COMMON_ENTITY_FIELDS
    | {"type_id", "type_name", "rarity_id", "attunement", "description"},
}
_OPTIONAL_ENTITY_FIELDS = {"equipaggiamento": {"mastery_id"}}
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
    "equipaggiamento": {
        "category_id",
        "subcategory_id",
        "subcategory_name",
    },
    "incantesimi": {"school_id", "casting_time", "range", "duration"},
    "oggetti_magici": {"type_id", "type_name", "rarity_id"},
}
_CONTENT_FIELDS = {
    "origini": {"description"},
    "specie": {"description"},
    "talenti": {"benefit"},
    "equipaggiamento": {"description"},
    "incantesimi": {"description", "at_higher_levels"},
    "classi": {"description"},
    "regole": {"content"},
    "oggetti_magici": {"description"},
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

            label_field = _LABEL_FIELDS.get(str(collection), "name")
            if not isinstance(item.get(label_field), str) or not item.get(label_field):
                errors.append(f"items[{index}].{label_field} is required")

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
                    required_fields = (
                        allowed_fields
                        - _COMMON_ENTITY_FIELDS
                        - _OPTIONAL_ENTITY_FIELDS.get(collection, set())
                    )
                    for field in sorted(required_fields):
                        if field not in item:
                            errors.append(f"items[{index}].{field} is required")
                    _validate_entity_fields(collection, item, index, errors)

    return errors


def _validate_provenance(
    value: Any,
    index: int,
    errors: list[str],
    *,
    prefix: str | None = None,
) -> None:
    prefix = prefix or f"items[{index}].provenance"
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

    if collection == "equipaggiamento":
        for field in ("cost", "weight"):
            if field in item:
                if field == "weight" and item[field] is None:
                    continue
                _validate_measure(item[field], f"items[{index}].{field}", errors)
        if "damage" in item:
            _validate_damage(item["damage"], f"items[{index}].damage", errors)
        if "property_ids" in item:
            property_ids = item["property_ids"]
            if not isinstance(property_ids, list) or not all(
                isinstance(value, str) and _SLUG.fullmatch(value)
                for value in property_ids
            ):
                errors.append(
                    f"items[{index}].property_ids must be a lowercase ASCII slug list"
                )
        if "mastery_id" in item and (
            not isinstance(item["mastery_id"], str)
            or _SLUG.fullmatch(item["mastery_id"]) is None
        ):
            errors.append(f"items[{index}].mastery_id must be a lowercase ASCII slug")

    if collection == "incantesimi":
        level = item.get("level")
        if "level" in item and (
            not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 9
        ):
            errors.append(f"items[{index}].level must be an integer from 0 to 9")
        for field in ("school_id",):
            if field in item and _SLUG.fullmatch(str(item[field])) is None:
                errors.append(f"items[{index}].{field} must be a lowercase ASCII slug")
        if "class_ids" in item:
            class_ids = item["class_ids"]
            if not isinstance(class_ids, list) or not all(
                isinstance(value, str) and _SLUG.fullmatch(value)
                for value in class_ids
            ):
                errors.append(
                    f"items[{index}].class_ids must be a lowercase ASCII slug list"
                )
        for field in ("ritual", "concentration"):
            if field in item and not isinstance(item[field], bool):
                errors.append(f"items[{index}].{field} must be a boolean")
        if "components" in item:
            _validate_components(
                item["components"],
                f"items[{index}].components",
                errors,
            )

    if collection == "classi":
        _validate_class(item, index, errors)

    if collection == "regole":
        parent_id = item.get("parent_id")
        if parent_id is not None and (
            not isinstance(parent_id, str) or _SLUG.fullmatch(parent_id) is None
        ):
            errors.append(
                f"items[{index}].parent_id must be null or a lowercase ASCII slug"
            )
        for field, minimum in (("depth", 1), ("order", 0)):
            value = item.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                errors.append(
                    f"items[{index}].{field} must be an integer >= {minimum}"
                )

    if collection == "oggetti_magici" and "attunement" in item:
        attunement = item["attunement"]
        prefix = f"items[{index}].attunement"
        if not isinstance(attunement, dict):
            errors.append(f"{prefix} must be an object")
        else:
            if set(attunement) != {"required", "requirement_text"}:
                errors.append(f"{prefix} must contain required and requirement_text")
            if not isinstance(attunement.get("required"), bool):
                errors.append(f"{prefix}.required must be a boolean")
            if not isinstance(attunement.get("requirement_text"), str):
                errors.append(f"{prefix}.requirement_text must be a string")
        for field in ("type_id", "rarity_id"):
            if not isinstance(item.get(field), str) or _SLUG.fullmatch(item[field]) is None:
                errors.append(f"items[{index}].{field} must be a lowercase ASCII slug")


def _slug_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(entry, str) and _SLUG.fullmatch(entry) for entry in value
    )


def _validate_class(item: dict[str, Any], index: int, errors: list[str]) -> None:
    prefix = f"items[{index}]"
    hit_die = item.get("hit_die")
    if not isinstance(hit_die, int) or isinstance(hit_die, bool) or hit_die <= 0:
        errors.append(f"{prefix}.hit_die must be a positive integer")

    progression = item.get("progression")
    if not isinstance(progression, list) or not progression:
        errors.append(f"{prefix}.progression must be a non-empty list")
    else:
        for row_index, row in enumerate(progression):
            row_prefix = f"{prefix}.progression[{row_index}]"
            if not isinstance(row, dict):
                errors.append(f"{row_prefix} must be an object")
                continue
            unknown = sorted(
                set(row) - {"level", "proficiency_bonus", "feature_ids", "resources"}
            )
            if unknown:
                errors.append(f"{row_prefix} has unknown fields: {', '.join(unknown)}")
            level = row.get("level")
            if not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 20:
                errors.append(f"{row_prefix}.level must be an integer from 1 to 20")
            bonus = row.get("proficiency_bonus")
            if not isinstance(bonus, int) or isinstance(bonus, bool):
                errors.append(f"{row_prefix}.proficiency_bonus must be an integer")
            if not _slug_list(row.get("feature_ids")):
                errors.append(
                    f"{row_prefix}.feature_ids must be a lowercase ASCII slug list"
                )
            resources = row.get("resources")
            if not isinstance(resources, list):
                errors.append(f"{row_prefix}.resources must be a list")
            else:
                for resource_index, resource in enumerate(resources):
                    resource_prefix = f"{row_prefix}.resources[{resource_index}]"
                    if not isinstance(resource, dict):
                        errors.append(f"{resource_prefix} must be an object")
                        continue
                    if set(resource) != {"id", "value"}:
                        errors.append(f"{resource_prefix} must contain id and value")
                    if not isinstance(resource.get("id"), str) or _SLUG.fullmatch(
                        resource["id"]
                    ) is None:
                        errors.append(f"{resource_prefix}.id must be a lowercase ASCII slug")
                    if not isinstance(resource.get("value"), str):
                        errors.append(f"{resource_prefix}.value must be a string")

    features = item.get("features")
    if not isinstance(features, list):
        errors.append(f"{prefix}.features must be a list")
    else:
        for feature_index, feature in enumerate(features):
            feature_prefix = f"{prefix}.features[{feature_index}]"
            if not isinstance(feature, dict):
                errors.append(f"{feature_prefix} must be an object")
                continue
            unknown = sorted(
                set(feature) - {"id", "name", "level", "provenance", "description"}
            )
            if unknown:
                errors.append(f"{feature_prefix} has unknown fields: {', '.join(unknown)}")
            if not isinstance(feature.get("id"), str) or _SLUG.fullmatch(
                feature["id"]
            ) is None:
                errors.append(f"{feature_prefix}.id must be a lowercase ASCII slug")
            if not isinstance(feature.get("name"), str) or not feature["name"]:
                errors.append(f"{feature_prefix}.name is required")
            level = feature.get("level")
            if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 20:
                errors.append(f"{feature_prefix}.level must be an integer from 0 to 20")
            _validate_provenance(
                feature.get("provenance"),
                index,
                errors,
                prefix=f"{feature_prefix}.provenance",
            )
            _validate_content(
                feature.get("description"),
                f"{feature_prefix}.description",
                errors,
            )

    if not isinstance(item.get("subclasses"), list):
        errors.append(f"{prefix}.subclasses must be a list")
    if not _slug_list(item.get("spell_ids")):
        errors.append(f"{prefix}.spell_ids must be a lowercase ASCII slug list")


def _validate_measure(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be an object")
        return
    unknown = sorted(set(value) - {"quantity", "unit"})
    if unknown:
        errors.append(f"{prefix} has unknown fields: {', '.join(unknown)}")
    quantity = value.get("quantity")
    if not isinstance(quantity, (int, float)) or isinstance(quantity, bool):
        errors.append(f"{prefix}.quantity must be a number")
    unit = value.get("unit")
    if not isinstance(unit, str) or _SLUG.fullmatch(unit) is None:
        errors.append(f"{prefix}.unit must be a lowercase ASCII slug")


def _validate_damage(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be an object")
        return
    unknown = sorted(set(value) - {"dice", "type_id"})
    if unknown:
        errors.append(f"{prefix} has unknown fields: {', '.join(unknown)}")
    dice = value.get("dice")
    if not isinstance(dice, str) or re.fullmatch(r"\d+(?:d\d+)?", dice) is None:
        errors.append(f"{prefix}.dice must be dice notation")
    type_id = value.get("type_id")
    if not isinstance(type_id, str) or _SLUG.fullmatch(type_id) is None:
        errors.append(f"{prefix}.type_id must be a lowercase ASCII slug")


def _validate_components(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} must be an object")
        return
    fields = {"verbal", "somatic", "material", "material_text"}
    unknown = sorted(set(value) - fields)
    if unknown:
        errors.append(f"{prefix} has unknown fields: {', '.join(unknown)}")
    for field in ("verbal", "somatic", "material"):
        if not isinstance(value.get(field), bool):
            errors.append(f"{prefix}.{field} must be a boolean")
    if not isinstance(value.get("material_text"), str):
        errors.append(f"{prefix}.material_text must be a string")


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
