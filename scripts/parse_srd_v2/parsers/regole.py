"""Parser for flat, addressable rule records."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


def _unique_path_id(path: list[str], used: set[str]) -> str:
    base = "-".join(slugify(part) for part in path if slugify(part))
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def _content(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    text = "\n\n".join(
        str(node.get("text", "")).strip()
        for node in nodes
        if node.get("type") == "paragraph" and str(node.get("text", "")).strip()
    )
    return [{"type": "text", "text": text}] if text else []


def parse_regole(section: dict[str, Any], source_id: str) -> ParseResult:
    """Flatten one source rule section while retaining parent relationships."""

    nodes = list(section.get("nodes", []))
    heading_indexes = [
        index for index, node in enumerate(nodes) if node.get("type") == "heading"
    ]
    stack: list[tuple[int, str, str]] = []
    sibling_orders: defaultdict[str | None, int] = defaultdict(int)
    used_ids: set[str] = set()
    items: list[dict[str, Any]] = []
    consumed_nodes: list[dict[str, Any]] = []
    ignored_nodes: list[dict[str, str]] = []

    for position, index in enumerate(heading_indexes):
        next_index = (
            heading_indexes[position + 1]
            if position + 1 < len(heading_indexes)
            else len(nodes)
        )
        heading = nodes[index]
        level = int(heading.get("heading_level") or 6)
        while stack and stack[-1][0] >= level:
            stack.pop()
        title = str(heading.get("text", "")).strip()
        path = [entry[1] for entry in stack] + [title]
        rule_id = _unique_path_id(path, used_ids)
        parent_id = stack[-1][2] if stack else None
        order = sibling_orders[parent_id]
        sibling_orders[parent_id] += 1

        body = nodes[index + 1 : next_index]
        paragraph_nodes = [node for node in body if node.get("type") == "paragraph"]
        other_nodes = [node for node in body if node.get("type") != "paragraph"]
        consumed_nodes.extend([heading, *paragraph_nodes])
        ignored_nodes.extend(ignored_node_entries(other_nodes, "unsupported_rule_node"))
        pages = [
            page
            for page in [heading.get("page_number"), *(node.get("page_number") for node in body)]
            if isinstance(page, int)
        ]
        items.append(
            {
                "id": rule_id,
                "title": title,
                "source_id": source_id,
                "provenance": {
                    "page_start": min(pages) if pages else section.get("page_start"),
                    "page_end": max(pages) if pages else section.get("page_end"),
                    "heading_path": path,
                    "section_id": section.get("id", ""),
                    "parser": "regole",
                },
                "parent_id": parent_id,
                "depth": len(stack) + 1,
                "order": order,
                "content": _content(paragraph_nodes),
            }
        )
        stack.append((level, title, rule_id))

    preamble = nodes[: heading_indexes[0]] if heading_indexes else nodes
    ignored_nodes = ignored_node_entries(preamble, "section_preamble") + ignored_nodes
    return ParseResult(
        items=items,
        consumed_node_ids=node_ids(consumed_nodes),
        ignored_nodes=ignored_nodes,
    )
