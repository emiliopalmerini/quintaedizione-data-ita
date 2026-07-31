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
_PRICE_TITLE_RE = re.compile(r"^(.+?)\s+\(([^()]*)\)$")
_ARMOR_SUBCATEGORY_RE = re.compile(
    r"^(Armatura (?:leggera|media|pesante)|Scudo)\s*\((.+)\)$",
    re.IGNORECASE,
)
_COLLAPSED_ARMOR_RE = re.compile(
    r"^(.+?)\s+(\+?\d+(?:\s+\+\s+modificatore di Des(?:\s+\(max 2\))?)?)"
    r"\s+(For \d+|—)\s+(Svantaggio|—)\s+([\d,.]+ kg)\s+([\d.]+ m[roa])$",
    re.IGNORECASE,
)
_COLLAPSED_TRANSPORT_RE = re.compile(
    r"^(.+?)\s+([\d,.]+ kg)\s+([\d.]+ m[roa])$", re.IGNORECASE
)
_COLLAPSED_VEHICLE_RE = re.compile(
    r"^(.+?)\s+([\d,.]+ km/h)\s+(\d+)\s+([\d—]+)\s+([\d/—]+)"
    r"\s+(\d+)\s+(\d+)\s+([\d—]+)\s+([\d.]+ mo)$",
    re.IGNORECASE,
)
_TRANSPORT_TITLES = {
    "Cavalcature e altri animali": "cavalcatura",
    "Veicoli aerei e imbarcazioni": "veicolo",
    "Finimenti e veicoli da tiro": "finimento",
}


def _cell_texts(row: dict[str, Any]) -> list[str]:
    return [str(cell.get("text", "")).strip() for cell in row.get("cells", [])]


def _header_ids(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(slugify(text) for text in _cell_texts(row))


def _quantity(text: str) -> dict[str, Any] | None:
    if text.strip() == "—":
        return None
    match = _QUANTITY_RE.fullmatch(text.strip())
    if match is None:
        return None
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


def _content(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    text = "\n\n".join(
        str(node.get("text", "")).strip()
        for node in nodes
        if node.get("type") == "paragraph" and str(node.get("text", "")).strip()
    )
    return [{"type": "text", "text": text}] if text else []


def _price(text: str) -> dict[str, Any] | None:
    normalized = text.strip().lower()
    if normalized == "gratis":
        return {"quantity": 0, "unit": "mo"}
    if "variabil" in normalized:
        return None
    return _quantity(text)


def _attribute(name: str, value: str) -> dict[str, str]:
    return {"id": slugify(name), "name": name, "value": value}


def _weapon_properties(text: str) -> tuple[list[str], list[dict[str, str]]]:
    property_ids: list[str] = []
    attributes: list[dict[str, str]] = []
    for raw_value in text.split(","):
        value = raw_value.strip()
        if not value:
            continue
        match = re.fullmatch(r"(.+?)\s*\((.+)\)", value)
        name = match.group(1).strip() if match else value
        property_id = slugify(name)
        if not property_id:
            continue
        property_ids.append(property_id)
        if match:
            attributes.append(_attribute(f"Proprietà: {name}", match.group(2).strip()))
    return property_ids, attributes


def _heading_items(
    nodes: list[dict[str, Any]], section: dict[str, Any], source_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    categories = {
        "Strumenti": "strumento",
        "Equipaggiamento d'avventura": "equipaggiamento-d-avventura",
        "Spese dello stile di vita": "servizio",
    }
    items: list[dict[str, Any]] = []
    consumed: list[dict[str, Any]] = []
    for index, heading in enumerate(nodes):
        if heading.get("type") != "heading":
            continue
        path = [str(part) for part in heading.get("heading_path", [])]
        category_name = next((name for name in categories if name in path), None)
        if category_name is None:
            continue
        level = int(heading.get("heading_level") or 6)
        if (category_name == "Spese dello stile di vita" and level != 4) or (
            category_name != "Spese dello stile di vita" and level != 5
        ):
            continue
        title_match = _PRICE_TITLE_RE.fullmatch(str(heading.get("text", "")).strip())
        if title_match is None:
            continue
        name, price_text = title_match.groups()
        end = index + 1
        while end < len(nodes):
            node = nodes[end]
            if node.get("type") == "heading" and int(node.get("heading_level") or 6) <= level:
                break
            end += 1
        body = [node for node in nodes[index + 1 : end] if node.get("type") == "paragraph"]
        attributes: list[dict[str, str]] = []
        weight = None
        for node in body:
            text = str(node.get("text", "")).strip()
            label, separator, value = text.partition(":")
            if not separator:
                continue
            if label.lower() == "peso":
                weight = _quantity(value.strip())
                if weight is None:
                    attributes.append(_attribute(label.strip(), value.strip()))
            else:
                attributes.append(_attribute(label.strip(), value.strip()))
        page_numbers = [
            page
            for page in [heading.get("page_number"), *(node.get("page_number") for node in body)]
            if isinstance(page, int)
        ]
        subcategory_name = path[-2] if len(path) > 1 else category_name
        cost = _price(price_text)
        if cost is None:
            attributes.append(_attribute("Prezzo", price_text))
        items.append(
            {
                "id": slugify(name),
                "name": name,
                "source_id": source_id,
                "provenance": {
                    "page_start": min(page_numbers),
                    "page_end": max(page_numbers),
                    "heading_path": [*path[:-1], name],
                    "section_id": section.get("id", ""),
                    "parser": "equipaggiamento",
                },
                "category_id": categories[category_name],
                "subcategory_id": slugify(subcategory_name),
                "subcategory_name": subcategory_name,
                "cost": cost,
                "weight": weight,
                "attributes": attributes,
                "description": _content(body),
            }
        )
        consumed.extend([heading, *body])
    return items, consumed


def _parse_armor_table(
    table: dict[str, Any], section: dict[str, Any], source_id: str
) -> list[dict[str, Any]]:
    if "Armature" not in table.get("heading_path", []):
        return []
    items: list[dict[str, Any]] = []
    subcategory_name = ""
    vestizione = ""
    for row in table.get("rows", []):
        cells = _cell_texts(row)
        populated = [value for value in cells if value]
        if not populated:
            continue
        subcategory = _ARMOR_SUBCATEGORY_RE.fullmatch(populated[0])
        if len(populated) == 1 and subcategory:
            subcategory_name, vestizione = subcategory.groups()
            continue
        if len(cells) == 6 and len(populated) > 1:
            name, armor_class, strength, stealth, weight, cost = cells
        else:
            collapsed = populated[0]
            suffix = ""
            if "\n" in collapsed:
                collapsed, suffix = collapsed.split("\n", 1)
            match = _COLLAPSED_ARMOR_RE.fullmatch(" ".join(collapsed.split()))
            if match is None:
                continue
            name, armor_class, strength, stealth, weight, cost = match.groups()
            if suffix:
                name = f"{name} {suffix.strip()}"
        attributes = [_attribute("Classe Armatura", armor_class)]
        if strength != "—":
            attributes.append(_attribute("Forza", strength))
        if stealth != "—":
            attributes.append(_attribute("Furtività", stealth))
        if vestizione:
            attributes.append(_attribute("Vestizione", vestizione))
        page_number = table.get("page_number", section.get("page_start"))
        items.append(
            {
                "id": slugify(name),
                "name": name,
                "source_id": source_id,
                "provenance": {
                    "page_start": page_number,
                    "page_end": page_number,
                    "heading_path": ["Equipaggiamento", "Armature", name],
                    "section_id": section.get("id", ""),
                    "parser": "equipaggiamento",
                },
                "category_id": "armatura",
                "subcategory_id": slugify(subcategory_name),
                "subcategory_name": subcategory_name,
                "cost": _quantity(cost),
                "weight": _quantity(weight),
                "attributes": attributes,
                "description": [],
            }
        )
    return items


def _transport_item(
    name: str,
    category_id: str,
    subcategory_name: str,
    cost: str,
    weight: str | None,
    attributes: list[dict[str, str]],
    page_number: int,
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any]:
    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": page_number,
            "page_end": page_number,
            "heading_path": ["Equipaggiamento", "Cavalcature e veicoli", subcategory_name, name],
            "section_id": section.get("id", ""),
            "parser": "equipaggiamento",
        },
        "category_id": category_id,
        "subcategory_id": slugify(subcategory_name),
        "subcategory_name": subcategory_name,
        "cost": _quantity(cost),
        "weight": _quantity(weight) if weight else None,
        "attributes": attributes,
        "description": [],
    }


def _parse_transport_rows(
    rows: list[dict[str, Any]],
    title: str,
    page_number: int,
    section: dict[str, Any],
    source_id: str,
    saddle_group: str = "",
) -> tuple[list[dict[str, Any]], str]:
    category_id = _TRANSPORT_TITLES[title]
    items: list[dict[str, Any]] = []
    for row in rows:
        cells = _cell_texts(row)
        populated = [value for value in cells if value]
        if not populated:
            continue
        if category_id == "veicolo":
            if len(populated) == 9:
                values = populated
            else:
                match = _COLLAPSED_VEHICLE_RE.fullmatch(" ".join(populated[0].split()))
                if match is None:
                    continue
                values = list(match.groups())
            name, speed, crew, passengers, cargo, ac, hp, threshold, cost = values
            labels = (
                "Velocità",
                "Equipaggio",
                "Passeggeri",
                "Carico",
                "CA",
                "PF",
                "Soglia di danno",
            )
            attributes = [
                _attribute(label, value)
                for label, value in zip(labels, values[1:-1], strict=True)
                if value != "—"
            ]
            weight = None
        else:
            if len(populated) == 1:
                if populated[0] == "Sella":
                    saddle_group = "Sella"
                    continue
                match = _COLLAPSED_TRANSPORT_RE.fullmatch(
                    " ".join(populated[0].split())
                )
                if match is None:
                    continue
                name, value, cost = match.groups()
            elif len(cells) >= 3:
                name, value, cost = cells[:3]
            else:
                continue
            if saddle_group and name in {"Da galoppo", "Esotica", "Militare"}:
                name = f"{saddle_group} {name.lower()}"
            if category_id == "cavalcatura":
                attributes = [_attribute("Capacità di trasporto", value)]
                weight = None
            else:
                attributes = []
                weight = value
        items.append(
            _transport_item(
                name,
                category_id,
                title,
                cost,
                weight,
                attributes,
                page_number,
                section,
                source_id,
            )
        )
    return items, saddle_group


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
        property_ids, property_attributes = _weapon_properties(properties)
        heading_path = ["Equipaggiamento", "Armi", subcategory_name, name]
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
                "property_ids": property_ids,
                "attributes": property_attributes,
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
    items, heading_nodes = _heading_items(nodes, section, source_id)
    consumed_node_ids = [
        node_id
        for node in heading_nodes
        if isinstance(node_id := node.get("id"), str)
    ]
    consumed_id_set = set(consumed_node_ids)
    ignored_nodes: list[dict[str, str]] = []
    subcategory_name = ""
    transport_title = ""
    saddle_group = ""
    seen_ids = {str(item["id"]) for item in items}
    for node in nodes:
        if node.get("id") in consumed_id_set:
            continue
        if node.get("type") != "table":
            text = str(node.get("text", "")).strip()
            if (
                node.get("type") == "heading"
                and transport_title
                and "Cavalcature e veicoli" not in node.get("heading_path", [])
            ):
                transport_title = ""
                saddle_group = ""
            if node.get("type") == "paragraph" and text in _TRANSPORT_TITLES:
                transport_title = text
            elif node.get("type") == "paragraph" and transport_title:
                transport_items, saddle_group = _parse_transport_rows(
                    [{"cells": [{"text": text}, {"text": ""}, {"text": ""}]}],
                    transport_title,
                    int(node.get("page_number") or section.get("page_start") or 0),
                    section,
                    source_id,
                    saddle_group,
                )
                if transport_items:
                    for item in transport_items:
                        if item["id"] not in seen_ids:
                            items.append(item)
                            seen_ids.add(item["id"])
                    node_id = node.get("id")
                    if isinstance(node_id, str):
                        consumed_node_ids.append(node_id)
                    continue
            path = [str(part).lower() for part in node.get("heading_path", [])]
            if node.get("type") == "paragraph" and "armi" in path:
                header_ids = set(slugify(text).split("-"))
                if {"nome", "danni", "proprieta", "padronanza", "peso", "costo"} <= header_ids:
                    ignored_nodes.extend(
                        ignored_node_entries([node], "repeated_table_header")
                    )
                    continue
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
        if transport_title:
            transport_items, saddle_group = _parse_transport_rows(
                node.get("rows", []),
                transport_title,
                int(node.get("page_number") or section.get("page_start") or 0),
                section,
                source_id,
                saddle_group,
            )
            if transport_items:
                for item in transport_items:
                    if item["id"] not in seen_ids:
                        items.append(item)
                        seen_ids.add(item["id"])
                node_id = node.get("id")
                if isinstance(node_id, str):
                    consumed_node_ids.append(node_id)
                continue
        armor_items = _parse_armor_table(node, section, source_id)
        if armor_items:
            for item in armor_items:
                if item["id"] not in seen_ids:
                    items.append(item)
                    seen_ids.add(item["id"])
            node_id = node.get("id")
            if isinstance(node_id, str):
                consumed_node_ids.append(node_id)
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
