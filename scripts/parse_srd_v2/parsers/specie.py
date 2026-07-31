"""Parser for Specie entities."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify


SPECIES_NAMES = (
    "Dragonide",
    "Elfo",
    "Gnomo",
    "Goliath",
    "Halfling",
    "Nano",
    "Orco",
    "Tiefling",
    "Umano",
)

_SPECIES_NAME_SET = set(SPECIES_NAMES)

_META_LABELS = {
    "tipo di creatura": "creature_type",
    "taglia": "size",
    "velocita": "speed",
    "velocità": "speed",
}

_TRAIT_NAMES = {
    "Agilità halfling",
    "Astuzia gnomesca",
    "Coraggioso",
    "Costituzione robusta",
    "Discendenza draconica",
    "Discendenza gigantica",
    "Esperto minatore",
    "Forma Grande",
    "Fortuna",
    "Furtività innata",
    "Intraprendente",
    "Lignaggio elfico",
    "Lignaggio gnomesco",
    "Pluriabilità",
    "Presenza ultraterrena",
    "Resilienza nanica",
    "Resistenza ai danni",
    "Resistenza implacabile",
    "Retaggio fatato",
    "Retaggio immondo",
    "Robustezza nanica",
    "Scarica di adrenalina",
    "Scurovisione",
    "Sensi acuti",
    "Soffio",
    "Trance",
    "Versatile",
    "Volo draconico",
}


def _content_segments(text: str) -> list[dict[str, str]]:
    if not text:
        return []
    return [{"type": "text", "text": text}]


def _is_heading(node: dict[str, Any]) -> bool:
    return node.get("type") == "heading"


def _is_species_heading(paragraph: dict[str, Any]) -> bool:
    text = str(paragraph.get("text", "")).strip()
    return _is_heading(paragraph) and text in _SPECIES_NAME_SET


def _normalized_label(text: str) -> str:
    return text.split(":", 1)[0].strip().lower()


def _clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ").strip()
    return re.sub(r"(?<=\d)(?=centimetri\b)", " ", text)


def _extract_meta(text: str) -> tuple[str, str] | None:
    label = _normalized_label(text)
    field = _META_LABELS.get(label)
    if field is None:
        return None
    if ":" not in text:
        return field, ""
    return field, text.split(":", 1)[1].strip()


def _append_continuation(value: str, continuation: str) -> str:
    continuation = _clean_text(continuation)
    if not value:
        return continuation
    value = _clean_text(value)
    if value.endswith(("\u00ad", "-")):
        return _clean_text(value[:-1] + continuation)
    return _clean_text(f"{value} {continuation}")


def _is_likely_field_continuation(value: str, text: str) -> bool:
    value = value.strip()
    text = text.strip()
    if not value or not text:
        return False
    if value.endswith((",", "o", "\u00ad", "-")):
        return True
    if text.startswith(("o ", "o\u00a0", "a tua scelta")):
        return True
    first = text[:1]
    return bool(first and first.islower())


def _extract_trait_start(text: str) -> tuple[str, str] | None:
    for name in sorted(_TRAIT_NAMES, key=len, reverse=True):
        prefix = f"{name}."
        if text.startswith(prefix):
            return name, text[len(prefix) :].strip()
    return None


def _append_text(value: str, text: str) -> str:
    text = text.strip()
    if not text:
        return value
    return _append_continuation(value, text)


def _build_species(
    name: str,
    heading: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any]:
    fields = {
        "creature_type": "",
        "size": "",
        "speed": "",
    }
    description = ""
    traits: list[dict[str, Any]] = []
    pages: list[int] = []
    current_field: str | None = None

    heading_page = heading.get("page_number")
    if isinstance(heading_page, int):
        pages.append(heading_page)

    for paragraph in body:
        page_number = paragraph.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)
        text = _clean_text(str(paragraph.get("text", "")))
        if not text or _is_heading(paragraph):
            continue

        meta = _extract_meta(text)
        if meta is not None:
            field, value = meta
            fields[field] = value
            current_field = field
            continue

        if current_field is not None and _is_likely_field_continuation(
            fields[current_field],
            text,
        ):
            fields[current_field] = _append_continuation(fields[current_field], text)
            continue
        current_field = None

        trait_start = _extract_trait_start(text)
        if trait_start is not None:
            trait_name, trait_text = trait_start
            if trait_text:
                traits.append({"name": trait_name, "description": trait_text})
            elif traits:
                traits[-1]["description"] = _append_text(traits[-1]["description"], text)
            else:
                description = _append_text(description, text)
            continue

        if traits:
            traits[-1]["description"] = _append_text(traits[-1]["description"], text)
        else:
            description = _append_text(description, text)

    page_start = min(pages) if pages else section.get("page_start")
    page_end = max(pages) if pages else section.get("page_end")

    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": page_start,
            "page_end": page_end,
            "heading_path": [section.get("title", ""), name],
            "section_id": section.get("id", ""),
            "parser": "specie",
        },
        **fields,
        "description": _content_segments(description),
        "traits": [
            {
                "name": trait["name"],
                "description": _content_segments(str(trait.get("description", ""))),
            }
            for trait in traits
        ],
    }


def parse_specie(section: dict[str, Any], source_id: str) -> list[dict[str, Any]]:
    """Parse Specie entities from one assigned section."""

    paragraphs = list(section.get("nodes", []))
    heading_indexes = [
        index for index, paragraph in enumerate(paragraphs) if _is_species_heading(paragraph)
    ]

    results: list[dict[str, Any]] = []
    for pos, index in enumerate(heading_indexes):
        next_index = (
            heading_indexes[pos + 1] if pos + 1 < len(heading_indexes) else len(paragraphs)
        )
        name = str(paragraphs[index].get("text", "")).strip()
        body = paragraphs[index + 1 : next_index]
        results.append(
            _build_species(
                name,
                paragraphs[index],
                body,
                section=section,
                source_id=source_id,
            )
        )

    return results
