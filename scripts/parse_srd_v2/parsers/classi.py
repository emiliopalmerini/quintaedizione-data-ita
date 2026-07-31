"""Parser for classes, progression rows, and class features."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


_HIT_DIE_RE = re.compile(r"Dado vita:?\s*d(\d+)", re.IGNORECASE)
_SPELL_SCHOOLS = (
    "Abiurazione",
    "Ammaliamento",
    "Divinazione",
    "Evocazione",
    "Illusione",
    "Invocazione",
    "Necromanzia",
    "Trasmutazione",
)
_SPELL_ROW_RE = re.compile(
    r"(?:^|\s+)(?:" + "|".join(_SPELL_SCHOOLS) + r")\s+"
    r"(?:[CMR](?:,\s*[CMR])*\b|[—–-])\s*",
    re.IGNORECASE,
)


def _cell_texts(row: dict[str, Any]) -> list[str]:
    return [str(cell.get("text", "")).strip() for cell in row.get("cells", [])]


def _is_progression_table(node: dict[str, Any]) -> bool:
    rows = node.get("rows", [])
    if node.get("type") != "table" or not rows:
        return False
    headers = [slugify(value) for value in _cell_texts(rows[0])]
    has_headers = len(headers) >= 3 and headers[:3] == [
        "livello", "bonus-di-competenza", "privilegi"
    ]
    cells = _cell_texts(rows[0])
    has_level_row = (
        len(cells) >= 3
        and cells[0].isdigit()
        and re.fullmatch(r"\+?\d+", cells[1]) is not None
    )
    return has_headers or has_level_row


def _class_ranges(nodes: list[dict[str, Any]]) -> list[tuple[int, int]]:
    heading_indexes = [
        index
        for index, node in enumerate(nodes)
        if node.get("type") == "heading" and node.get("heading_level") == 2
    ]
    ranges = []
    for position, index in enumerate(heading_indexes):
        end = heading_indexes[position + 1] if position + 1 < len(heading_indexes) else len(nodes)
        if any(_is_progression_table(node) for node in nodes[index + 1 : end]):
            ranges.append((index, end))
    return ranges


def _progression_headers(
    nodes: list[dict[str, Any]], table_index: int
) -> list[str]:
    table = nodes[table_index]
    rows = table.get("rows", [])
    if not rows:
        return []
    cells = rows[0].get("cells", [])
    cell_texts = _cell_texts(rows[0])
    if [slugify(value) for value in cell_texts[:3]] == [
        "livello",
        "bonus-di-competenza",
        "privilegi",
    ]:
        return cell_texts
    headers = ["Livello", "Bonus di competenza", "Privilegi"] + [
        "" for _ in cells[3:]
    ]
    table_bbox = table.get("bbox", [])
    if len(table_bbox) != 4:
        return headers
    table_top = float(table_bbox[1])
    page_number = table.get("page_number")
    span_groups: list[list[tuple[float, float, str]]] = [
        [] for _ in cells
    ]
    for node in nodes[:table_index]:
        if node.get("page_number") != page_number:
            continue
        for span in node.get("spans", []):
            bbox = span.get("bbox", [])
            if len(bbox) != 4 or not table_top - 30 <= float(bbox[3]) <= table_top:
                continue
            center = (float(bbox[0]) + float(bbox[2])) / 2
            for column, cell in enumerate(cells):
                cell_bbox = cell.get("bbox", [])
                if len(cell_bbox) == 4 and float(cell_bbox[0]) <= center <= float(cell_bbox[2]):
                    span_groups[column].append(
                        (float(bbox[1]), float(bbox[0]), str(span.get("text", "")).strip())
                    )
                    break
    for column in range(3, len(headers)):
        values = [value for _, _, value in sorted(span_groups[column]) if value]
        if values:
            headers[column] = " ".join(values)
        else:
            headers[column] = f"resource-{column - 2}"
    return headers


def _parse_progression(
    table: dict[str, Any],
    class_id: str,
    source_headers: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows = table.get("rows", [])
    first_cells = _cell_texts(rows[0])
    has_headers = [slugify(value) for value in first_cells[:3]] == [
        "livello", "bonus-di-competenza", "privilegi"
    ]
    column_count = len(first_cells)
    headers = source_headers or (
        first_cells
        if has_headers
        else ["Livello", "Bonus di competenza", "Privilegi"]
        + [f"resource-{index}" for index in range(1, column_count - 2)]
    )
    progression = []
    feature_levels: dict[str, int] = {}
    for row in rows[1:] if has_headers else rows:
        cells = _cell_texts(row)
        populated = [value for value in cells if value]
        if len(populated) == 1 and column_count > 3:
            parts = populated[0].split()
            resource_count = column_count - 3
            if len(parts) >= resource_count + 3:
                cells = [
                    parts[0],
                    parts[1],
                    " ".join(parts[2:-resource_count]),
                    *parts[-resource_count:],
                ]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        level = int(cells[0])
        feature_names = [value.strip() for value in cells[2].split(",") if value.strip()]
        feature_ids = []
        for name in feature_names:
            feature_slug = slugify(name)
            if not feature_slug:
                continue
            feature_id = f"{class_id}-{feature_slug}"
            feature_ids.append(feature_id)
            feature_levels.setdefault(feature_slug, level)
        progression.append(
            {
                "level": level,
                "proficiency_bonus": int(cells[1].lstrip("+")),
                "feature_ids": feature_ids,
                "resources": [
                    {"id": slugify(header), "value": cells[column]}
                    for column, header in enumerate(headers[3:], start=3)
                    if column < len(cells) and cells[column]
                ],
            }
        )
    return progression, feature_levels


def _content(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    text = "\n\n".join(
        str(node.get("text", "")).strip()
        for node in nodes
        if node.get("type") == "paragraph" and str(node.get("text", "")).strip()
    )
    return [{"type": "text", "text": text}] if text else []


def _spell_list_names(nodes: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    pending_name = False
    for node in nodes:
        if not any(
            "Lista degli incantesimi" in str(part)
            for part in node.get("heading_path", [])
        ):
            continue
        texts = []
        if node.get("type") == "table":
            texts = [" ".join(_cell_texts(row)) for row in node.get("rows", [])]
        elif node.get("type") == "paragraph":
            texts = [str(node.get("text", ""))]
        for text in texts:
            normalized = " ".join(text.replace("\n", " ").split())
            if pending_name and not _SPELL_ROW_RE.search(normalized):
                if normalized and normalized not in names:
                    names.append(normalized)
                pending_name = False
                continue
            if not _SPELL_ROW_RE.search(normalized):
                continue
            name = _SPELL_ROW_RE.sub(" ", normalized).strip()
            if not name:
                pending_name = True
                continue
            if name and name not in names:
                names.append(name)
    return names


def _parse_features(
    nodes: list[dict[str, Any]],
    class_id: str,
    feature_levels: dict[str, int],
    section: dict[str, Any],
) -> list[dict[str, Any]]:
    indexes = [
        index
        for index, node in enumerate(nodes)
        if node.get("type") == "heading" and node.get("heading_level") == 5
        and not any(
            str(part).lower().startswith("diventare un")
            for part in node.get("heading_path", [])
        )
    ]
    features = []
    parsed_names = []
    for index in indexes:
        raw_name = str(nodes[index].get("text", "")).strip()
        level_match = re.match(r"Livello\s+(\d+):\s*(.+)", raw_name, re.IGNORECASE)
        parsed_names.append(level_match.group(2).strip() if level_match else raw_name)
    for position, index in enumerate(indexes):
        end = index + 1
        while end < len(nodes):
            node = nodes[end]
            if node.get("type") == "heading" and int(node.get("heading_level") or 6) <= 5:
                break
            end += 1
        heading = nodes[index]
        raw_name = str(heading.get("text", "")).strip()
        level_match = re.match(r"Livello\s+(\d+):\s*(.+)", raw_name, re.IGNORECASE)
        name = level_match.group(2).strip() if level_match else raw_name
        body = nodes[index + 1 : end]
        pages = [
            page
            for page in [heading.get("page_number"), *(node.get("page_number") for node in body)]
            if isinstance(page, int)
        ]
        feature_id = f"{class_id}-{slugify(name)}"
        level = (
            int(level_match.group(1))
            if level_match
            else feature_levels.get(slugify(name), 0)
        )
        if parsed_names.count(name) > 1:
            feature_id = f"{feature_id}-{level}"
        features.append(
            {
                "id": feature_id,
                "name": name,
                "level": level,
                "provenance": {
                    "page_start": min(pages) if pages else section.get("page_start"),
                    "page_end": max(pages) if pages else section.get("page_end"),
                    "heading_path": heading.get("heading_path", []),
                    "section_id": section.get("id", ""),
                    "parser": "classi",
                },
                "description": _content(body),
            }
        )
    return features


def _parse_subclasses(
    nodes: list[dict[str, Any]], class_id: str, section: dict[str, Any]
) -> list[dict[str, Any]]:
    marker_indexes = [
        index
        for index, node in enumerate(nodes)
        if node.get("type") == "heading"
        and node.get("heading_level") == 4
        and str(node.get("text", "")).lower().startswith("sottoclasse")
    ]
    subclasses: list[dict[str, Any]] = []
    for marker_position, marker_index in enumerate(marker_indexes):
        marker = nodes[marker_index]
        marker_text = str(marker.get("text", "")).strip()
        _, _, inline_name = marker_text.partition(":")
        name_index = marker_index
        name = inline_name.strip()
        if not name and marker_index + 1 < len(nodes):
            candidate = nodes[marker_index + 1]
            if candidate.get("type") == "heading" and candidate.get("heading_level") == 4:
                name_index = marker_index + 1
                name = str(candidate.get("text", "")).strip()
        if not name:
            continue
        end = marker_indexes[marker_position + 1] if marker_position + 1 < len(marker_indexes) else len(nodes)
        for index in range(name_index + 1, end):
            node = nodes[index]
            if node.get("type") == "heading" and node.get("heading_level") == 4:
                end = index
                break
        subclass_id = f"{class_id}-{slugify(name)}"
        feature_indexes = [
            index
            for index in range(name_index + 1, end)
            if nodes[index].get("type") == "heading"
            and nodes[index].get("heading_level") == 5
            and re.match(r"Livello\s+\d+:", str(nodes[index].get("text", "")), re.IGNORECASE)
        ]
        features: list[dict[str, Any]] = []
        for position, index in enumerate(feature_indexes):
            feature_end = feature_indexes[position + 1] if position + 1 < len(feature_indexes) else end
            heading = nodes[index]
            match = re.match(
                r"Livello\s+(\d+):\s*(.+)",
                str(heading.get("text", "")).strip(),
                re.IGNORECASE,
            )
            if match is None:
                continue
            level, feature_name = match.groups()
            body = nodes[index + 1 : feature_end]
            pages = [
                page
                for page in [heading.get("page_number"), *(node.get("page_number") for node in body)]
                if isinstance(page, int)
            ]
            features.append(
                {
                    "id": f"{subclass_id}-{slugify(feature_name)}",
                    "name": feature_name,
                    "level": int(level),
                    "provenance": {
                        "page_start": min(pages) if pages else section.get("page_start"),
                        "page_end": max(pages) if pages else section.get("page_end"),
                        "heading_path": heading.get("heading_path", []),
                        "section_id": section.get("id", ""),
                        "parser": "classi",
                    },
                    "description": _content(body),
                }
            )
        description_nodes = nodes[name_index + 1 : feature_indexes[0] if feature_indexes else end]
        pages = [
            page
            for page in [marker.get("page_number"), *(node.get("page_number") for node in nodes[marker_index:end])]
            if isinstance(page, int)
        ]
        subclasses.append(
            {
                "id": subclass_id,
                "name": name,
                "provenance": {
                    "page_start": min(pages) if pages else section.get("page_start"),
                    "page_end": max(pages) if pages else section.get("page_end"),
                    "heading_path": [*marker.get("heading_path", [])[:-1], name],
                    "section_id": section.get("id", ""),
                    "parser": "classi",
                },
                "description": _content(description_nodes),
                "features": features,
            }
        )
    return subclasses


def _parse_class(
    nodes: list[dict[str, Any]],
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any]:
    heading = nodes[0]
    name = str(heading.get("text", "")).strip()
    class_id = slugify(name)
    hit_die = 0
    progression: list[dict[str, Any]] = []
    feature_levels: dict[str, int] = {}
    for index, node in enumerate(nodes[1:], start=1):
        node_text = str(node.get("text", ""))
        if node.get("type") == "table":
            node_text = " ".join(
                text
                for row in node.get("rows", [])
                for text in _cell_texts(row)
            )
        match = _HIT_DIE_RE.search(node_text)
        if match is not None:
            hit_die = int(match.group(1))
        if _is_progression_table(node) and not progression:
            progression_table = node
            if index + 1 < len(nodes):
                overflow_text = str(nodes[index + 1].get("text", "")).strip()
                if re.match(r"20\s+\+6\s+", overflow_text):
                    column_count = len(_cell_texts(node.get("rows", [])[0]))
                    overflow_parts = overflow_text.split()
                    resource_count = column_count - 3
                    if len(overflow_parts) >= resource_count + 3:
                        overflow_cells = [
                            {"text": overflow_text},
                            *({"text": ""} for _ in range(column_count - 1)),
                        ]
                    else:
                        level, bonus, feature = overflow_text.split(maxsplit=2)
                        overflow_cells = [
                            {"text": level},
                            {"text": bonus},
                            {"text": feature},
                            *({"text": ""} for _ in range(column_count - 3)),
                        ]
                    progression_table = {
                        **node,
                        "rows": [
                            *node.get("rows", []),
                            {
                                "cells": overflow_cells
                            },
                        ],
                    }
            progression, feature_levels = _parse_progression(
                progression_table,
                class_id,
                _progression_headers(nodes, index),
            )

    pages: list[int] = []
    for node in nodes:
        page_number = node.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)
    subclass_start = next(
        (
            index
            for index, node in enumerate(nodes)
            if node.get("type") == "heading"
            and node.get("heading_level") == 4
            and str(node.get("text", "")).lower().startswith("sottoclasse")
        ),
        len(nodes),
    )
    features = _parse_features(
        nodes[:subclass_start], class_id, feature_levels, section
    )
    subclasses = _parse_subclasses(nodes, class_id, section)
    known_features = {
        feature["id"]: feature
        for feature in [
            *features,
            *(feature for subclass in subclasses for feature in subclass["features"]),
        ]
    }
    for row in progression:
        level_feature_ids = [
            feature["id"] for feature in features if feature["level"] == row["level"]
        ]
        level_feature_ids.extend(
            feature["id"]
            for subclass in subclasses
            for feature in subclass["features"]
            if feature["level"] == row["level"]
        )
        if level_feature_ids:
            row["feature_ids"] = level_feature_ids
            continue
        resolved_ids = []
        for feature_id in row["feature_ids"]:
            if feature_id in known_features:
                resolved_ids.append(feature_id)
                continue
            source_parts = feature_id.split("-")
            candidates = []
            for known_id in known_features:
                known_parts = known_id.split("-")
                shared = 0
                for source_part, known_part in zip(source_parts, known_parts, strict=False):
                    if source_part != known_part:
                        break
                    shared += 1
                if shared >= 2:
                    candidates.append((shared, known_id))
            if candidates:
                resolved_ids.append(max(candidates)[1])
            else:
                resolved_ids.append(feature_id)
        row["feature_ids"] = list(dict.fromkeys(resolved_ids))
    return {
        "id": class_id,
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": min(pages) if pages else section.get("page_start"),
            "page_end": max(pages) if pages else section.get("page_end"),
            "heading_path": heading.get("heading_path", []),
            "section_id": section.get("id", ""),
            "parser": "classi",
        },
        "hit_die": hit_die,
        "progression": progression,
        "features": features,
        "subclasses": subclasses,
        "spell_ids": [],
        "_spell_names": _spell_list_names(nodes),
        "description": [],
    }


def parse_classi(section: dict[str, Any], source_id: str) -> ParseResult:
    """Parse class regions identified by their progression tables."""

    nodes = list(section.get("nodes", []))
    ranges = _class_ranges(nodes)
    consumed_indexes = {
        index for start, end in ranges for index in range(start, end)
    }
    items = [_parse_class(nodes[start:end], section, source_id) for start, end in ranges]
    first_class = ranges[0][0] if ranges else len(nodes)
    ignored = ignored_node_entries(nodes[:first_class], "section_preamble")
    ignored.extend(
        ignored_node_entries(
            [node for index, node in enumerate(nodes) if index >= first_class and index not in consumed_indexes],
            "outside_class_boundary",
        )
    )
    return ParseResult(
        items=items,
        consumed_node_ids=node_ids(
            [node for index, node in enumerate(nodes) if index in consumed_indexes]
        ),
        ignored_nodes=ignored,
    )
