"""Shared parser for monster and animal stat blocks."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


_SIZES = {
    "minuscola": "minuscola",
    "minuscolo": "minuscola",
    "piccola": "piccola",
    "piccolo": "piccola",
    "media": "media",
    "medio": "media",
    "grande": "grande",
    "enorme": "enorme",
    "mastodontica": "mastodontica",
    "mastodontico": "mastodontica",
}
_STATS_RE = re.compile(
    r"CA\s+(\d+).*?Iniziativa\s+([^P]+?)\s+PF\s+(\d+)\s+"
    r"\(([^)]+)\)\s+Velocità\s+(.+)$",
    re.IGNORECASE,
)
_DETAIL_RE = re.compile(r"(Abilità|Sensi|Lingue|GS)\s+", re.IGNORECASE)
_CATEGORY_FIELDS = {
    "tratti": "traits",
    "azioni": "actions",
    "azioni bonus": "bonus_actions",
    "azione bonus": "bonus_actions",
    "reazioni": "reactions",
    "azioni leggendarie": "legendary_actions",
}


def _content(text: str) -> list[dict[str, str]]:
    return [{"type": "text", "text": text}] if text else []


def _heading_path(node: dict[str, Any]) -> list[str]:
    path: list[str] = []
    for value in node.get("heading_path", []):
        text = str(value)
        if not path or path[-1] != text:
            path.append(text)
    return path


def _details(text: str) -> dict[str, str]:
    matches = list(_DETAIL_RE.finditer(text))
    result = {"skills": "", "senses": "", "languages": "", "challenge_rating": ""}
    fields = {
        "abilità": "skills",
        "sensi": "senses",
        "lingue": "languages",
        "gs": "challenge_rating",
    }
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[match.end() : end].strip()
        field = fields[match.group(1).lower()]
        result[field] = value.split(" ", 1)[0] if field == "challenge_rating" else value
    return result


def _abilities(table: dict[str, Any]) -> dict[str, int]:
    scores: dict[str, int] = {}
    for row in table.get("rows", []):
        cells = [str(cell.get("text", "")) for cell in row.get("cells", [])]
        for index in (0, 4, 8):
            if index >= len(cells):
                continue
            match = re.fullmatch(r"(For|Des|Cos|Int|Sag|Car)\s+(\d+)", cells[index])
            if match:
                scores[match.group(1).lower()] = int(match.group(2))
    return scores


def _feature_parts(node: dict[str, Any], text: str) -> tuple[str, str] | None:
    spans = node.get("spans", [])
    if spans:
        first = spans[0]
        title = str(first.get("text", "")).strip()
        if not isinstance(first.get("flags"), int) or not first["flags"] & 16:
            return None
        return title.rstrip("."), text[len(title) :].lstrip(". ")
    if "." not in text:
        return None
    name, _, description = text.partition(".")
    return name, description.lstrip()


def _features(nodes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result = {field: [] for field in set(_CATEGORY_FIELDS.values())}
    current_field: str | None = None
    for node in nodes:
        if node.get("type") == "heading" and node.get("heading_level") == 6:
            current_field = _CATEGORY_FIELDS.get(str(node.get("text", "")).lower())
            continue
        if current_field is None or node.get("type") != "paragraph":
            continue
        text = str(node.get("text", "")).strip()
        parts = _feature_parts(node, text)
        if parts is not None:
            name, description = parts
            result[current_field].append(
                {
                    "id": slugify(name),
                    "name": name,
                    "description": _content(description),
                }
            )
        elif result[current_field]:
            segments = result[current_field][-1]["description"]
            if segments:
                segments[0]["text"] = f"{segments[0]['text']} {text}"
    return result


def _parse_stat_block(
    nodes: list[dict[str, Any]],
    section: dict[str, Any],
    source_id: str,
    collection_id: str,
) -> dict[str, Any] | None:
    if len(nodes) < 5:
        return None
    heading = nodes[0]
    subtitle = str(nodes[1].get("text", "")).strip()
    before_alignment, _, alignment = subtitle.partition(",")
    parts = before_alignment.split()
    size_index = next(
        (i for i, value in enumerate(parts) if value.lower() in _SIZES), -1
    )
    if size_index < 0:
        return None
    creature_type = " ".join(parts[:size_index])
    size = parts[size_index]

    stats_match = _STATS_RE.search(str(nodes[2].get("text", "")))
    if stats_match is None:
        return None
    ac, initiative, hp_average, hp_formula, speed = stats_match.groups()
    ability_table = next((node for node in nodes if node.get("type") == "table"), {})
    detail_node = next(
        (
            node
            for node in nodes[3:]
            if node.get("type") == "paragraph"
            and "GS " in str(node.get("text", ""))
        ),
        {},
    )
    details = _details(str(detail_node.get("text", "")))
    feature_data = _features(nodes[3:])
    pages: list[int] = []
    for node in nodes:
        page_number = node.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)
    name = str(heading.get("text", "")).strip()
    path = _heading_path(heading)
    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": min(pages) if pages else section.get("page_start"),
            "page_end": max(pages) if pages else section.get("page_end"),
            "heading_path": path,
            "section_id": section.get("id", ""),
            "parser": collection_id,
        },
        "collection_id": collection_id,
        "group": path[-2] if len(path) > 1 else "",
        "creature_type_id": slugify(creature_type),
        "size_id": _SIZES[size.lower()],
        "alignment": alignment.strip(),
        "ac": int(ac),
        "initiative": initiative.strip(),
        "hp": {"average": int(hp_average), "formula": hp_formula.strip()},
        "speed": speed.strip(),
        "ability_scores": _abilities(ability_table),
        **details,
        **feature_data,
    }


def _parse_collection(
    section: dict[str, Any], source_id: str, collection_id: str
) -> ParseResult:
    nodes = list(section.get("nodes", []))
    indexes = [
        index
        for index, node in enumerate(nodes)
        if node.get("type") == "heading" and node.get("heading_level") == 3
    ]
    items = []
    consumed = []
    for position, index in enumerate(indexes):
        end = indexes[position + 1] if position + 1 < len(indexes) else len(nodes)
        if (
            position + 1 < len(indexes)
            and end > index
            and nodes[end - 1].get("type") == "heading"
            and nodes[end - 1].get("heading_level") == 2
            and nodes[end - 1].get("text")
            == nodes[indexes[position + 1]].get("text")
        ):
            end -= 1
        block = nodes[index:end]
        item = _parse_stat_block(block, section, source_id, collection_id)
        if item is not None:
            items.append(item)
            consumed.extend(block)
    first = indexes[0] if indexes else len(nodes)
    ignored = ignored_node_entries(nodes[:first], "section_preamble")
    consumed_ids = set(node_ids(consumed))
    ignored.extend(
        ignored_node_entries(
            [node for node in nodes[first:] if node.get("id") not in consumed_ids],
            "unrecognized_stat_block",
        )
    )
    return ParseResult(
        items=items,
        consumed_node_ids=node_ids(consumed),
        ignored_nodes=ignored,
    )


def parse_mostri(section: dict[str, Any], source_id: str) -> ParseResult:
    return _parse_collection(section, source_id, "mostri")


def parse_animali(section: dict[str, Any], source_id: str) -> ParseResult:
    return _parse_collection(section, source_id, "animali")
