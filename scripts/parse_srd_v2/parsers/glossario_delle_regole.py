"""Parser for addressable rules glossary entries."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


_DESCRIPTOR_RE = re.compile(r"^(.*?)\s*\[([^]]+)]$")
_QUOTED_RE = re.compile(r'"([^"]+)"')


def _content(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    text = "\n\n".join(
        str(node.get("text", "")).strip()
        for node in nodes
        if node.get("type") == "paragraph" and str(node.get("text", "")).strip()
    )
    return [{"type": "text", "text": text}] if text else []


def _related_terms(text: str) -> list[str]:
    if "Vedi anche" not in text:
        return []
    clause = text.split("Vedi anche", 1)[1].split(".", 1)[0]
    terms = []
    for match in _QUOTED_RE.finditer(clause):
        before = clause[: match.start()].rstrip()
        after = clause[match.end() :].lstrip()
        if before.endswith("(") or after.startswith("("):
            continue
        terms.append(match.group(1))
    return terms


def parse_glossario(section: dict[str, Any], source_id: str) -> ParseResult:
    nodes = list(section.get("nodes", []))
    indexes = [
        index
        for index, node in enumerate(nodes)
        if node.get("type") == "heading" and node.get("heading_level") == 5
    ]
    catalog: dict[str, tuple[str, str]] = {}
    for index in indexes:
        term = str(nodes[index].get("text", "")).strip()
        match = _DESCRIPTOR_RE.fullmatch(term)
        base_term = match.group(1).strip() if match else term
        catalog[base_term.casefold()] = (slugify(term), base_term)

    items: list[dict[str, Any]] = []
    consumed: list[dict[str, Any]] = []
    ignored: list[dict[str, str]] = []
    for position, index in enumerate(indexes):
        end = indexes[position + 1] if position + 1 < len(indexes) else len(nodes)
        heading = nodes[index]
        body = nodes[index + 1 : end]
        paragraphs = [node for node in body if node.get("type") == "paragraph"]
        ignored.extend(
            ignored_node_entries(
                [node for node in body if node.get("type") != "paragraph"],
                "unsupported_glossary_node",
            )
        )
        consumed.extend([heading, *paragraphs])
        term = str(heading.get("text", "")).strip()
        match = _DESCRIPTOR_RE.fullmatch(term)
        descriptor_id = slugify(match.group(2)) if match else None
        text = " ".join(str(node.get("text", "")) for node in paragraphs)
        related: list[dict[str, str]] = []
        for quoted in _related_terms(text):
            target = catalog.get(quoted.casefold())
            if target is None or target[0] == slugify(term):
                continue
            related.append(
                {
                    "source_id": source_id,
                    "collection": "glossario_delle_regole",
                    "id": target[0],
                    "text": quoted,
                }
            )
        pages = [
            page
            for page in [heading.get("page_number"), *(n.get("page_number") for n in body)]
            if isinstance(page, int)
        ]
        items.append(
            {
                "id": slugify(term),
                "term": term,
                "source_id": source_id,
                "provenance": {
                    "page_start": min(pages),
                    "page_end": max(pages),
                    "heading_path": heading.get("heading_path", [term]),
                    "section_id": section.get("id", ""),
                    "parser": "glossario_delle_regole",
                },
                "descriptor_id": descriptor_id,
                "content": _content(paragraphs),
                "related_entry_refs": related,
            }
        )

    preamble = nodes[: indexes[0]] if indexes else nodes
    ignored = ignored_node_entries(preamble, "section_preamble") + ignored
    return ParseResult(items, node_ids(consumed), ignored)
