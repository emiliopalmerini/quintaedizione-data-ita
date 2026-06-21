"""Normalization stage for parser v2."""

from __future__ import annotations

from typing import Any


def normalize_extracted(extracted: dict[str, Any]) -> dict[str, Any]:
    """Build a minimal normalized document model from extracted pages."""

    pages = []
    for page in extracted.get("pages", []):
        paragraphs = []
        for block in page.get("blocks", []):
            for line in block.get("lines", []):
                text = "".join(span.get("text", "") for span in line.get("spans", []))
                text = text.strip()
                if not text:
                    continue
                paragraphs.append(
                    {
                        "text": text,
                        "role": "unknown",
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
