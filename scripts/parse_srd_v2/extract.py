"""PDF extraction stage for parser v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import DependencyUnavailable
from .manifest import SourceMetadata, source_metadata
from .profiles import SRD_521_IT, SourceProfile, validate_source_profile


def _fitz_module() -> Any:
    try:
        import fitz  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise DependencyUnavailable(
            "PyMuPDF is required for PDF extraction. "
            "Run through nix-shell with python313Packages.pymupdf."
        ) from exc
    return fitz


def _span_to_json(span: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": span.get("text", ""),
        "font": span.get("font", ""),
        "size": round(float(span.get("size", 0)), 2),
        "color": span.get("color", 0),
        "flags": span.get("flags", 0),
        "ascender": span.get("ascender"),
        "descender": span.get("descender"),
        "origin": list(span.get("origin", ())),
        "bbox": list(span.get("bbox", ())),
    }


def _word_to_json(word: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "text": str(word[4]),
        "bbox": [float(value) for value in word[:4]],
        "block_index": int(word[5]),
        "line_index": int(word[6]),
        "word_index": int(word[7]),
    }


def _table_to_json(table: Any) -> dict[str, Any]:
    extracted_rows = table.extract()
    rows = []
    for row_index, row in enumerate(table.rows):
        texts = extracted_rows[row_index] if row_index < len(extracted_rows) else []
        cells = []
        for cell_index, bbox in enumerate(row.cells):
            text = texts[cell_index] if cell_index < len(texts) else ""
            cells.append(
                {
                    "bbox": list(bbox) if bbox is not None else [],
                    "text": str(text or "").strip(),
                }
            )
        rows.append({"cells": cells})
    return {"bbox": list(table.bbox), "rows": rows}


def extract_pdf(
    pdf_path: Path,
    *,
    profile: SourceProfile = SRD_521_IT,
) -> tuple[SourceMetadata, dict[str, Any]]:
    """Extract raw layout artifacts from a source PDF."""

    fitz = _fitz_module()
    doc = fitz.open(str(pdf_path))
    font_names: set[str] = set()
    pages: list[dict[str, Any]] = []

    for page_index, page in enumerate(doc):
        page_number = page_index + 1
        page_dict = page.get_text("dict")
        page_entry: dict[str, Any] = {
            "page_number": page_number,
            "width": page.rect.width,
            "height": page.rect.height,
            "text": page.get_text("text"),
            "words": [_word_to_json(word) for word in page.get_text("words")],
            "tables": [_table_to_json(table) for table in page.find_tables().tables],
            "blocks": [],
        }

        for block_index, block in enumerate(page_dict.get("blocks", [])):
            if block.get("type") != 0:
                continue
            block_entry: dict[str, Any] = {
                "block_index": block_index,
                "bbox": list(block.get("bbox", ())),
                "lines": [],
            }
            for line in block.get("lines", []):
                line_entry: dict[str, Any] = {
                    "bbox": list(line.get("bbox", ())),
                    "writing_mode": line.get("wmode", 0),
                    "direction": list(line.get("dir", (1.0, 0.0))),
                    "spans": [],
                }
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    font = span.get("font", "")
                    if font:
                        font_names.add(font)
                    line_entry["spans"].append(_span_to_json(span))
                if line_entry["spans"]:
                    block_entry["lines"].append(line_entry)
            if block_entry["lines"]:
                page_entry["blocks"].append(block_entry)

        pages.append(page_entry)

    validate_source_profile(profile, page_count=len(doc), font_names=font_names)

    metadata = source_metadata(pdf_path, profile=profile, page_count=len(doc))
    artifact = {
        "stage": "extracted",
        "source": {
            "id": metadata.id,
            "title": metadata.title,
            "checksum_sha256": metadata.checksum_sha256,
            "page_count": metadata.page_count,
            "profile": metadata.profile,
        },
        "profile": profile.name,
        "font_names": sorted(font_names),
        "pages": pages,
    }
    return metadata, artifact
