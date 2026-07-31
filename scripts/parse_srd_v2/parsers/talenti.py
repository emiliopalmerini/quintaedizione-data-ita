"""Parser for Talenti entities."""

from __future__ import annotations

import re
from typing import Any

from ..slugify import slugify
from .result import ParseResult, ignored_node_entries, node_ids


def _content_segments(text: str) -> list[dict[str, str]]:
    text = _output_text(text)
    if not text:
        return []
    return [{"type": "text", "text": text}]


def _clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    return text.strip()


def _output_text(text: str) -> str:
    return _clean_text(text).replace("\u00ad", "")


def _append_text(value: str, text: str) -> str:
    text = _clean_text(text)
    if not text:
        return value
    value = _clean_text(value)
    if not value:
        return text
    if value.endswith(("\u00ad", "-")):
        return _clean_text(value[:-1] + text)
    return f"{value} {text}"


def _is_heading(node: dict[str, Any]) -> bool:
    return node.get("type") == "heading"


def _is_talent_heading(paragraph: dict[str, Any]) -> bool:
    path = [str(part) for part in paragraph.get("heading_path", [])]
    return (
        _is_heading(paragraph)
        and paragraph.get("heading_level") == 5
        and "Descrizioni dei talenti" in path
        and len(path) >= 4
    )


def _has_open_parenthesis(text: str) -> bool:
    return text.count("(") > text.count(")")


def _parse_metadata(metadata_parts: list[str]) -> tuple[str, str]:
    metadata = ""
    for part in metadata_parts:
        metadata = _append_text(metadata, part)
    if not metadata.startswith("Talento "):
        return "", ""

    rest = metadata.removeprefix("Talento ").strip()
    prerequisite = ""
    match = re.search(r"\s*\(\s*prerequisito:\s*(.*?)\s*\)\s*$", rest)
    if match is not None:
        prerequisite = match.group(1).strip()
        rest = rest[: match.start()].strip()
    return rest, prerequisite


def _collect_metadata_and_benefit(body: list[dict[str, Any]]) -> tuple[list[str], str, list[int]]:
    metadata_parts: list[str] = []
    benefit = ""
    pages: list[int] = []
    collecting_metadata = True

    for paragraph in body:
        page_number = paragraph.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)
        text = _clean_text(str(paragraph.get("text", "")))
        if not text or _is_heading(paragraph):
            continue

        if collecting_metadata:
            if not metadata_parts and text.startswith("Talento "):
                metadata_parts.append(text)
                if not _has_open_parenthesis(text):
                    collecting_metadata = False
                continue
            if metadata_parts and _has_open_parenthesis(" ".join(metadata_parts)):
                metadata_parts.append(text)
                if not _has_open_parenthesis(" ".join(metadata_parts)):
                    collecting_metadata = False
                continue
            collecting_metadata = False

        benefit = _append_text(benefit, text)

    return metadata_parts, benefit, pages


def _build_talent(
    name: str,
    heading: dict[str, Any],
    body: list[dict[str, Any]],
    *,
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any]:
    metadata_parts, benefit, pages = _collect_metadata_and_benefit(body)
    category, prerequisite = _parse_metadata(metadata_parts)
    if not category:
        path = [str(part) for part in heading.get("heading_path", [])]
        if len(path) >= 2 and path[-2].startswith("Talenti "):
            category = path[-2].removeprefix("Talenti ")
        prerequisite_match = re.search(
            r"Talento\s+.+?\(\s*prerequisito:\s*(.*?)\s*\)", benefit
        )
        if prerequisite_match is not None:
            prerequisite = prerequisite_match.group(1)

    heading_page = heading.get("page_number")
    if isinstance(heading_page, int):
        pages.append(heading_page)

    page_start = min(pages) if pages else section.get("page_start")
    page_end = max(pages) if pages else section.get("page_end")

    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": page_start,
            "page_end": page_end,
            "heading_path": heading.get("heading_path")
            or [section.get("title", ""), name],
            "section_id": section.get("id", ""),
            "parser": "talenti",
        },
        "category": category,
        "prerequisite": prerequisite,
        "repeatable": "Ripetibile." in benefit,
        "benefit": _content_segments(benefit),
    }


def parse_talenti(section: dict[str, Any], source_id: str) -> ParseResult:
    """Parse Talenti entities from one assigned section."""

    paragraphs = list(section.get("nodes", []))
    heading_indexes = [
        index for index, paragraph in enumerate(paragraphs) if _is_talent_heading(paragraph)
    ]

    results: list[dict[str, Any]] = []
    for pos, index in enumerate(heading_indexes):
        next_index = (
            heading_indexes[pos + 1] if pos + 1 < len(heading_indexes) else len(paragraphs)
        )
        name = str(paragraphs[index].get("text", "")).strip()
        body = paragraphs[index + 1 : next_index]
        results.append(
            _build_talent(
                name,
                paragraphs[index],
                body,
                section=section,
                source_id=source_id,
            )
        )

    first_heading = heading_indexes[0] if heading_indexes else len(paragraphs)
    return ParseResult(
        items=results,
        consumed_node_ids=node_ids(paragraphs[first_heading:]),
        ignored_nodes=ignored_node_entries(
            paragraphs[:first_heading],
            "section_preamble",
        ),
    )
