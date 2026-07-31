"""Parser for magic items under the alphabetical source section."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


_SUBTITLE_RE = re.compile(
    r"^(.+?),\s*(comune|non comune|rar[oa]|molto rar[oa]|leggendari[oa]|manufatto|varia)"
    r"(?:\s*\(richiede sintonia(?:\s+(.+?))?\))?\s*$",
    re.IGNORECASE,
)
_RARITY_IDS = {
    "comune": "comune",
    "non comune": "non-comune",
    "raro": "raro",
    "rara": "raro",
    "molto raro": "molto-raro",
    "molto rara": "molto-raro",
    "leggendario": "leggendario",
    "leggendaria": "leggendario",
    "manufatto": "manufatto",
    "varia": "varia",
}


def _is_item_heading(node: dict[str, Any]) -> bool:
    path = [str(part).lower() for part in node.get("heading_path", [])]
    return (
        node.get("type") == "heading"
        and node.get("heading_level") == 5
        and any("oggetti magici a" in part and "z" in part for part in path)
    )


def _content(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    text = "\n\n".join(
        str(node.get("text", "")).strip()
        for node in nodes
        if node.get("type") == "paragraph" and str(node.get("text", "")).strip()
    )
    return [{"type": "text", "text": text}] if text else []


def _build_item(
    heading: dict[str, Any],
    body: list[dict[str, Any]],
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any] | None:
    paragraphs = [node for node in body if node.get("type") == "paragraph"]
    if not paragraphs:
        return None
    subtitle = " ".join(str(paragraphs[0].get("text", "")).split())
    match = _SUBTITLE_RE.fullmatch(subtitle)
    if match is None:
        return None
    type_name, rarity, requirement = match.groups()
    pages = [
        page
        for page in [heading.get("page_number"), *(node.get("page_number") for node in body)]
        if isinstance(page, int)
    ]
    name = str(heading.get("text", "")).strip()
    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": min(pages) if pages else section.get("page_start"),
            "page_end": max(pages) if pages else section.get("page_end"),
            "heading_path": heading.get("heading_path", []),
            "section_id": section.get("id", ""),
            "parser": "oggetti_magici",
        },
        "type_id": slugify(type_name),
        "type_name": type_name,
        "rarity_id": _RARITY_IDS[rarity.lower()],
        "attunement": {
            "required": "richiede sintonia" in subtitle.lower(),
            "requirement_text": requirement.strip() if requirement else "",
        },
        "description": _content(paragraphs[1:]),
    }


def parse_oggetti_magici(section: dict[str, Any], source_id: str) -> ParseResult:
    """Parse magic items and explicitly account for embedded table nodes."""

    nodes = list(section.get("nodes", []))
    indexes = [index for index, node in enumerate(nodes) if _is_item_heading(node)]
    items: list[dict[str, Any]] = []
    consumed_nodes: list[dict[str, Any]] = []
    ignored_nodes: list[dict[str, str]] = []
    for position, index in enumerate(indexes):
        end = indexes[position + 1] if position + 1 < len(indexes) else len(nodes)
        heading = nodes[index]
        body = nodes[index + 1 : end]
        item = _build_item(heading, body, section, source_id)
        if item is not None:
            items.append(item)
        consumed_nodes.extend([heading, *(node for node in body if node.get("type") == "paragraph")])
        ignored_nodes.extend(
            ignored_node_entries(
                [node for node in body if node.get("type") != "paragraph"],
                "unsupported_magic_item_node",
            )
        )

    preamble = nodes[: indexes[0]] if indexes else nodes
    ignored_nodes = ignored_node_entries(preamble, "section_preamble") + ignored_nodes
    return ParseResult(
        items=items,
        consumed_node_ids=node_ids(consumed_nodes),
        ignored_nodes=ignored_nodes,
    )
