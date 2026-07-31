"""Parser for classes, progression rows, and class features."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


_HIT_DIE_RE = re.compile(r"Dado vita:?\s*d(\d+)", re.IGNORECASE)


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


def _parse_progression(
    table: dict[str, Any],
    class_id: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows = table.get("rows", [])
    first_cells = _cell_texts(rows[0])
    has_headers = [slugify(value) for value in first_cells[:3]] == [
        "livello", "bonus-di-competenza", "privilegi"
    ]
    column_count = len(first_cells)
    headers = (
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
    ]
    features = []
    for position, index in enumerate(indexes):
        end = indexes[position + 1] if position + 1 < len(indexes) else len(nodes)
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
        features.append(
            {
                "id": f"{class_id}-{slugify(name)}",
                "name": name,
                "level": (
                    int(level_match.group(1))
                    if level_match
                    else feature_levels.get(slugify(name), 0)
                ),
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
    for node in nodes[1:]:
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
            progression, feature_levels = _parse_progression(node, class_id)

    pages: list[int] = []
    for node in nodes:
        page_number = node.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)
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
        "features": _parse_features(nodes, class_id, feature_levels, section),
        "subclasses": [],
        "spell_ids": [],
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
