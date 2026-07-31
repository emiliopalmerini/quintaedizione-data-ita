"""Parser for structured equipment table nodes."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries


_WEAPON_HEADERS = ("nome", "costo", "danni", "peso", "proprieta", "padronanza")
_QUANTITY_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s+(.+)$")
_DAMAGE_RE = re.compile(r"^(\d+d\d+)\s+(.+)$", re.IGNORECASE)


def _cell_texts(row: dict[str, Any]) -> list[str]:
    return [str(cell.get("text", "")).strip() for cell in row.get("cells", [])]


def _header_ids(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(slugify(text) for text in _cell_texts(row))


def _quantity(text: str) -> dict[str, Any]:
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
    return {"dice": dice.lower(), "type_id": slugify(damage_type)}


def _parse_weapon_table(
    table: dict[str, Any],
    section: dict[str, Any],
    source_id: str,
) -> list[dict[str, Any]]:
    rows = table.get("rows", [])
    if not rows or _header_ids(rows[0]) != _WEAPON_HEADERS:
        return []

    items: list[dict[str, Any]] = []
    subcategory_name = ""
    for row in rows[1:]:
        cells = _cell_texts(row)
        if len(cells) != len(_WEAPON_HEADERS):
            continue
        populated = [text for text in cells if text]
        if len(populated) == 1 and cells[0]:
            subcategory_name = cells[0]
            continue
        if not cells[0]:
            continue

        name, cost, damage, weight, properties, mastery = cells
        heading_path = list(table.get("heading_path", []))
        heading_path.append(name)
        page_number = table.get("page_number", section.get("page_start"))
        items.append(
            {
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
                    slugify(value)
                    for value in properties.split(",")
                    if value.strip()
                ],
                "mastery_id": slugify(mastery),
                "description": [],
            }
        )
    return items


def parse_equipaggiamento(section: dict[str, Any], source_id: str) -> ParseResult:
    """Parse supported equipment tables and account for source nodes."""

    nodes = list(section.get("nodes", []))
    items: list[dict[str, Any]] = []
    consumed_node_ids: list[str] = []
    ignored_nodes: list[dict[str, str]] = []
    for node in nodes:
        if node.get("type") != "table":
            ignored_nodes.extend(ignored_node_entries([node], "section_preamble"))
            continue
        table_items = _parse_weapon_table(node, section, source_id)
        if not table_items:
            ignored_nodes.extend(ignored_node_entries([node], "unsupported_table"))
            continue
        items.extend(table_items)
        node_id = node.get("id")
        if isinstance(node_id, str):
            consumed_node_ids.append(node_id)

    return ParseResult(
        items=items,
        consumed_node_ids=consumed_node_ids,
        ignored_nodes=ignored_nodes,
    )
