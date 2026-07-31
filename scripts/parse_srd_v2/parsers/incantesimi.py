"""Parser for structurally discovered spell definitions."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


_CANTRIP_RE = re.compile(r"Trucchetto\s+di\s+(.+?)\s*\((.+?)\)", re.IGNORECASE)
_LEVELED_RE = re.compile(
    r"(.+?)\s+di\s+(\d+)[º°]\s+livello\s*\((.+?)\)",
    re.IGNORECASE,
)
_HIGHER_LEVELS_MARKER = "Utilizzo di uno slot incantesimo di livello superiore."
_FIELD_LABELS = {
    "tempo di lancio": "casting_time",
    "gittata": "range",
    "componenti": "components",
    "componente": "components",
    "durata": "duration",
}


def _content(texts: list[str]) -> list[dict[str, str]]:
    text = "\n\n".join(text.strip() for text in texts if text.strip())
    return [{"type": "text", "text": text}] if text else []


def _is_spell_heading(node: dict[str, Any]) -> bool:
    path = [str(part).lower() for part in node.get("heading_path", [])]
    return (
        node.get("type") == "heading"
        and node.get("heading_level") == 5
        and "descrizioni degli incantesimi" in path
    )


def _parse_subtitle(text: str) -> tuple[int, str, list[str]] | None:
    normalized = " ".join(text.split())
    match = _CANTRIP_RE.search(normalized)
    if match is not None:
        school, classes = match.groups()
        return 0, slugify(school), [slugify(value) for value in classes.split(",")]
    match = _LEVELED_RE.search(normalized)
    if match is None:
        return None
    school, level, classes = match.groups()
    return int(level), slugify(school), [slugify(value) for value in classes.split(",")]


def _metadata_field(text: str) -> tuple[str, str] | None:
    if ":" not in text:
        return None
    label, value = text.split(":", 1)
    field = _FIELD_LABELS.get(label.strip().lower())
    return (field, value.strip()) if field is not None else None


def _components(text: str) -> dict[str, Any]:
    upper = text.upper()
    material_match = re.search(r"\bM\s*\((.*)\)\s*$", text, re.IGNORECASE)
    return {
        "verbal": bool(re.search(r"(?:^|[,\s])V(?:$|[,\s])", upper)),
        "somatic": bool(re.search(r"(?:^|[,\s])S(?:$|[,\s])", upper)),
        "material": bool(re.search(r"(?:^|[,\s])M(?:$|[,\s(])", upper)),
        "material_text": material_match.group(1).strip() if material_match else "",
    }


def _build_spell(
    heading: dict[str, Any],
    body: list[dict[str, Any]],
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any] | None:
    if not body:
        return None
    subtitle = _parse_subtitle(str(body[0].get("text", "")))
    if subtitle is None:
        return None
    level, school_id, class_ids = subtitle

    fields = {"casting_time": "", "range": "", "components": "", "duration": ""}
    description_parts: list[str] = []
    higher_parts: list[str] = []
    in_higher_levels = False
    pages = [heading.get("page_number")]
    for node in body[1:]:
        pages.append(node.get("page_number"))
        text = str(node.get("text", "")).strip()
        metadata = _metadata_field(text)
        if metadata is not None and not description_parts:
            field, value = metadata
            fields[field] = value
            continue
        if text.startswith(_HIGHER_LEVELS_MARKER):
            in_higher_levels = True
            remainder = text.removeprefix(_HIGHER_LEVELS_MARKER).strip()
            if remainder:
                higher_parts.append(remainder)
            continue
        if in_higher_levels:
            higher_parts.append(text)
        elif text:
            description_parts.append(text)

    valid_pages = [page for page in pages if isinstance(page, int)]
    name = str(heading.get("text", "")).strip()
    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": min(valid_pages) if valid_pages else section.get("page_start"),
            "page_end": max(valid_pages) if valid_pages else section.get("page_end"),
            "heading_path": heading.get("heading_path")
            or [section.get("title", ""), name],
            "section_id": section.get("id", ""),
            "parser": "incantesimi",
        },
        "level": level,
        "school_id": school_id,
        "class_ids": class_ids,
        "casting_time": fields["casting_time"],
        "range": fields["range"],
        "components": _components(fields["components"]),
        "duration": fields["duration"],
        "ritual": "rituale" in fields["casting_time"].lower(),
        "concentration": "concentrazione" in fields["duration"].lower(),
        "description": _content(description_parts),
        "at_higher_levels": _content(higher_parts),
    }


def parse_incantesimi(section: dict[str, Any], source_id: str) -> ParseResult:
    """Parse spell definitions below the descriptions heading."""

    nodes = list(section.get("nodes", []))
    heading_indexes = [index for index, node in enumerate(nodes) if _is_spell_heading(node)]
    items: list[dict[str, Any]] = []
    consumed_indexes: set[int] = set()
    for position, index in enumerate(heading_indexes):
        next_index = (
            heading_indexes[position + 1]
            if position + 1 < len(heading_indexes)
            else len(nodes)
        )
        consumed_indexes.update(range(index, next_index))
        item = _build_spell(nodes[index], nodes[index + 1 : next_index], section, source_id)
        if item is not None:
            items.append(item)

    first_heading = heading_indexes[0] if heading_indexes else len(nodes)
    consumed_nodes = [node for index, node in enumerate(nodes) if index in consumed_indexes]
    ignored = ignored_node_entries(nodes[:first_heading], "section_preamble")
    return ParseResult(
        items=items,
        consumed_node_ids=node_ids(consumed_nodes),
        ignored_nodes=ignored,
    )
