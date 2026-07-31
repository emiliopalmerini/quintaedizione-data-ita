"""Parser for Origini entities."""

from __future__ import annotations

from typing import Any

from ..slugify import slugify


_META_LABELS = {
    "punteggi di caratteristica": "ability_scores",
    "talento": "feat",
    "competenze nelle abilita": "skill_proficiencies",
    "competenze nelle abilit\u00e0": "skill_proficiencies",
    "competenza negli strumenti": "tool_proficiency",
    "equipaggiamento": "equipment",
}

_SKIP_HEADINGS = {
    "origini",
    "origini dei personaggi",
    "origine dei personaggi",
    "descrizioni delle origini",
    "elementi di un'origine",
    "elementi di una origine",
    "specie",
    "specie dei personaggi",
    "descrizioni delle specie",
}

_BOUNDARY_HEADINGS = {
    "specie",
    "specie dei personaggi",
    "descrizioni delle specie",
}


def _content_segments(text: str) -> list[dict[str, str]]:
    if not text:
        return []
    return [{"type": "text", "text": text}]


def _normalized_label(text: str) -> str:
    return text.split(":", 1)[0].strip().lower()


def _extract_meta(text: str) -> tuple[str, str] | None:
    label = _normalized_label(text)
    field = _META_LABELS.get(label)
    if field is None:
        return None
    if ":" not in text:
        return field, ""
    return field, text.split(":", 1)[1].strip()


def _append_continuation(value: str, continuation: str) -> str:
    continuation = continuation.strip()
    if not value:
        return continuation
    value = value.strip()
    if value.endswith(("\u00ad", "-")):
        return value[:-1] + continuation
    return f"{value} {continuation}"


def _is_likely_field_continuation(value: str, text: str) -> bool:
    value = value.strip()
    text = text.strip()
    if not value or not text:
        return False
    if value.endswith((",", " e", " capitolo", "\u00ad", "-")):
        return True
    if text.startswith(("\"", "(", "o (")):
        return True
    first = text[:1]
    return bool(first and first.islower())


def _is_heading(node: dict[str, Any]) -> bool:
    return node.get("type") == "heading"


def _has_metadata_before_next_heading(
    paragraphs: list[dict[str, Any]],
    start_index: int,
) -> bool:
    for paragraph in paragraphs[start_index + 1 :]:
        if _is_heading(paragraph):
            return False
        if _extract_meta(str(paragraph.get("text", ""))) is not None:
            return True
    return False


def _is_origin_heading(paragraphs: list[dict[str, Any]], index: int) -> bool:
    paragraph = paragraphs[index]
    if not _is_heading(paragraph):
        return False
    title = str(paragraph.get("text", "")).strip()
    if not title or title.lower() in _SKIP_HEADINGS:
        return False
    return _has_metadata_before_next_heading(paragraphs, index)


def _next_boundary_index(paragraphs: list[dict[str, Any]], start_index: int) -> int:
    for index, paragraph in enumerate(paragraphs[start_index + 1 :], start=start_index + 1):
        if _is_heading(paragraph):
            text = str(paragraph.get("text", "")).strip().lower()
            if text in _BOUNDARY_HEADINGS:
                return index
    return len(paragraphs)


def _build_origin(
    name: str,
    body: list[dict[str, Any]],
    *,
    section: dict[str, Any],
    source_id: str,
) -> dict[str, Any]:
    fields = {
        "ability_scores": "",
        "feat": "",
        "skill_proficiencies": "",
        "tool_proficiency": "",
        "equipment": "",
    }
    description_parts: list[str] = []
    pages: list[int] = []
    current_field: str | None = None

    for paragraph in body:
        page_number = paragraph.get("page_number")
        if isinstance(page_number, int):
            pages.append(page_number)
        text = str(paragraph.get("text", "")).strip()
        if not text:
            continue
        meta = _extract_meta(text)
        if meta is not None:
            field, value = meta
            fields[field] = value
            current_field = field
            continue
        if current_field is not None and _is_likely_field_continuation(
            fields[current_field],
            text,
        ):
            fields[current_field] = _append_continuation(fields[current_field], text)
            continue
        current_field = None
        if not _is_heading(paragraph):
            description_parts.append(text)

    page_start = min(pages) if pages else section.get("page_start")
    page_end = max(pages) if pages else section.get("page_end")
    description = "\n\n".join(description_parts)

    return {
        "id": slugify(name),
        "name": name,
        "source_id": source_id,
        "provenance": {
            "page_start": page_start,
            "page_end": page_end,
            "heading_path": [section.get("title", ""), name],
            "section_id": section.get("id", ""),
            "parser": "origini",
        },
        **fields,
        "description": _content_segments(description),
    }


def parse_origini(section: dict[str, Any], source_id: str) -> list[dict[str, Any]]:
    """Parse Origini entities from one assigned section."""

    paragraphs = list(section.get("nodes", []))
    heading_indexes = [
        index for index, paragraph in enumerate(paragraphs) if _is_origin_heading(paragraphs, index)
    ]

    results: list[dict[str, Any]] = []
    for pos, index in enumerate(heading_indexes):
        next_heading = heading_indexes[pos + 1] if pos + 1 < len(heading_indexes) else len(paragraphs)
        next_boundary = _next_boundary_index(paragraphs, index)
        next_index = min(next_heading, next_boundary)
        name = str(paragraphs[index].get("text", "")).strip()
        body = paragraphs[index + 1 : next_index]
        results.append(_build_origin(name, body, section=section, source_id=source_id))

    return results
