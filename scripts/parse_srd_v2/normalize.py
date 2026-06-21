"""Normalization stage for parser v2."""

from __future__ import annotations

from typing import Any


_HEADING_COLOR = 0x8C2220


def _classify_paragraph(spans: list[dict[str, Any]]) -> tuple[str, int | None]:
    """Classify a paragraph role from extracted line spans."""

    heading_spans = [
        span
        for span in spans
        if span.get("color") == _HEADING_COLOR and "GillSans" in span.get("font", "")
    ]
    if not heading_spans:
        return "body", None

    max_size = max(float(span.get("size", 0)) for span in heading_spans)
    if max_size >= 23:
        return "heading", 1
    if max_size >= 16:
        return "heading", 2
    if max_size >= 14:
        return "heading", 3
    if max_size >= 12:
        return "heading", 5
    return "heading", 6


def normalize_extracted(extracted: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal normalized document model from extracted pages."""

    pages = []
    for page in extracted.get("pages", []):
        paragraphs = []
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = "".join(span.get("text", "") for span in spans)
                text = text.strip()
                if not text:
                    continue
                role, heading_level = _classify_paragraph(spans)
                paragraphs.append(
                    {
                        "text": text,
                        "role": role,
                        "heading_level": heading_level,
                        "page_number": page.get("page_number"),
                        "bbox": line.get("bbox", []),
                    }
                )
        pages.append(
            {
                "page_number": page.get("page_number"),
                "width": page.get("width"),
                "height": page.get("height"),
                "paragraphs": paragraphs,
            }
        )

    return {
        "schema_version": "2.0.0",
        "stage": "normalized",
        "source": extracted.get("source", {}),
        "pages": pages,
    }
