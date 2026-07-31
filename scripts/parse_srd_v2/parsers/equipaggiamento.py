"""Parser for structured equipment table nodes."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries


_WEAPON_HEADERS = ("nome", "costo", "danni", "peso", "proprieta", "padronanza")
_QUANTITY_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s+(.+)$")
_DAMAGE_RE = re.compile(
    r"^(\d+(?:d\d+)?)\s+(contundente|contundenti|perforante|perforanti|tagliente|taglienti)$",
    re.IGNORECASE,
)
_MASTERY_NAMES = (
    "Colpo di striscio",
    "Doppio fendente",
    "Rovesciamento",
    "Vessazione",
    "Fiaccare",
    "Graffio",
    "Lentezza",
    "Spinta",
)
_COLLAPSED_WEAPON_RE = re.compile(
    r"^(.+?)\s+(\d+(?:d\d+)?\s+\S+)\s+(.+?)\s+("
    + "|".join(re.escape(name) for name in _MASTERY_NAMES)
    + r")\s+((?:\d+(?:[.,]\d+)?\s+kg|—))\s+(\d+(?:[.,]\d+)?\s+\S+)$",
    re.IGNORECASE,
)


def _cell_texts(row: dict[str, Any]) -> list[str]:
    return [str(cell.get("text", "")).strip() for cell in row.get("cells", [])]


def _header_ids(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(slugify(text) for text in _cell_texts(row))


def _quantity(text: str) -> dict[str, Any] | None:
    if text.strip() == "—":
        return None
    match = _QUANTITY_RE.fullmatch(text.strip())
    if match is None:
        return {"quantity": text, "unit": ""}
    raw_quantity, raw_unit = match.groups()
    quantity = float(raw_quantity.replace(",", "."))
    if quantity.is_integer():
        quantity = int(quantity)
    return {"quantity": quantity, "unit": slugify(raw_unit)}


def _damage(text: str) -> dict[str, str]:
    match = _DAMAGE_RE.fullmatch(text.strip())
    if match is None:
        return {"dice": "", "type_id": slugify(text)}
    dice, damage_type = match.groups()
    type_id = {
        "contundente": "contundenti",
        "perforante": "perforanti",
        "tagliente": "taglienti",
    }.get(damage_type.lower(), slugify(damage_type))
    return {"dice": dice.lower(), "type_id": type_id}


def _real_weapon_cells(cells: list[str]) -> list[str] | None:
    populated = [text for text in cells if text]
    if len(populated) >= 5 and len(cells) == 6 and _DAMAGE_RE.fullmatch(cells[1]):
        name, damage, properties, mastery, weight, cost = cells
        return [name, cost, damage, weight, properties, mastery]
    if len(populated) != 1:
        return None
    text = " ".join(populated[0].split())
    trailing_property = ""
    if text.lower().endswith(" ricarica"):
        text = text[: -len(" ricarica")]
        trailing_property = "ricarica"
    text = re.sub(
        r"\bDoppio\s+((?:\d+(?:[.,]\d+)?\s+kg|—)\s+\d+(?:[.,]\d+)?\s+\S+)\s+fendente$",
        r"Doppio fendente \1",
        text,
        flags=re.IGNORECASE,
    )
    match = _COLLAPSED_WEAPON_RE.fullmatch(text)
    if match is None:
        return None
    name, damage, properties, mastery, weight, cost = match.groups()
    if trailing_property:
        properties = f"{properties}, {trailing_property}"
    return [name, cost, damage, weight, properties, mastery]


def _parse_weapon_table(
    table: dict[str, Any],
    section: dict[str, Any],
    source_id: str,
    subcategory_name: str = "",
) -> tuple[list[dict[str, Any]], str]:
    rows = table.get("rows", [])
    if not rows:
        return [], subcategory_name
    has_header = _header_ids(rows[0]) == _WEAPON_HEADERS
    first_cells = _cell_texts(rows[0])
    looks_like_weapon_table = has_header or (
        len(first_cells) == 6
        and (
            len([value for value in first_cells if value]) == 1
            or _real_weapon_cells(first_cells) is not None
        )
    )
    if not looks_like_weapon_table:
        return [], subcategory_name

    items: list[dict[str, Any]] = []
    for row in rows[1:] if has_header else rows:
        cells = _cell_texts(row)
        if len(cells) != len(_WEAPON_HEADERS):
            continue
        populated = [text for text in cells if text]
        if len(populated) == 1 and cells[0]:
            parsed_cells = _real_weapon_cells(cells)
            if parsed_cells is None:
                subcategory_name = cells[0]
                continue
            cells = parsed_cells
        elif not has_header:
            parsed_cells = _real_weapon_cells(cells)
            if parsed_cells is None:
                continue
            cells = parsed_cells
        if not cells[0]:
            continue

        name, cost, damage, weight, properties, mastery = cells
        heading_path = list(table.get("heading_path", []))
        heading_path.append(name)
        page_number = table.get("page_number", section.get("page_start"))
        item = {
                "id": slugify(name),
                "name": name,
                "source_id": source_id,
                "provenance": {
                    "page_start": page_number,
                    "page_end": page_number,
                    "heading_path": heading_path,
                    "section_id": section.get("id", ""),
                    "parser": "equipaggiamento",
                },
                "category_id": "arma",
                "subcategory_id": slugify(subcategory_name),
                "subcategory_name": subcategory_name,
                "cost": _quantity(cost),
                "weight": _quantity(weight),
                "damage": _damage(damage),
                "property_ids": [
                    property_id
                    for value in properties.split(",")
                    if (property_id := slugify(value))
                ],
                "description": [],
            }
        mastery_id = slugify(mastery)
        if mastery_id:
            item["mastery_id"] = mastery_id
        items.append(item)
    return items, subcategory_name


def parse_equipaggiamento(section: dict[str, Any], source_id: str) -> ParseResult:
    """Parse supported equipment tables and account for source nodes."""

    nodes = list(section.get("nodes", []))
    items: list[dict[str, Any]] = []
    consumed_node_ids: list[str] = []
    ignored_nodes: list[dict[str, str]] = []
    subcategory_name = ""
    seen_ids: set[str] = set()
    for node in nodes:
        if node.get("type") != "table":
            path = [str(part).lower() for part in node.get("heading_path", [])]
            if node.get("type") == "paragraph" and "armi" in path:
                table_items, subcategory_name = _parse_weapon_table(
                    {
                        "rows": [{"cells": [{"text": node.get("text", "")}, *({"text": ""} for _ in range(5))]}],
                        "heading_path": node.get("heading_path", []),
                        "page_number": node.get("page_number"),
                    },
                    section,
                    source_id,
                    subcategory_name,
                )
                if table_items:
                    for item in table_items:
                        if item["id"] not in seen_ids:
                            items.append(item)
                            seen_ids.add(item["id"])
                    node_id = node.get("id")
                    if isinstance(node_id, str):
                        consumed_node_ids.append(node_id)
                    continue
            ignored_nodes.extend(ignored_node_entries([node], "section_preamble"))
            continue
        table_items, subcategory_name = _parse_weapon_table(
            node,
            section,
            source_id,
            subcategory_name,
        )
        if not table_items:
            ignored_nodes.extend(ignored_node_entries([node], "unsupported_table"))
            continue
        for item in table_items:
            if item["id"] not in seen_ids:
                items.append(item)
                seen_ids.add(item["id"])
        node_id = node.get("id")
        if isinstance(node_id, str):
            consumed_node_ids.append(node_id)

    return ParseResult(
        items=items,
        consumed_node_ids=consumed_node_ids,
        ignored_nodes=ignored_nodes,
    )
