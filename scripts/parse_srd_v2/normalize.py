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

    primary = max(heading_spans, key=lambda span: float(span.get("size", 0)))
    max_size = float(primary.get("size", 0))
    font = str(primary.get("font", ""))
    emphasized = any(weight in font for weight in ("SemiBold", "Semibold", "Bold"))
    if not emphasized:
        return "heading", 6
    if max_size >= 23:
        return "heading", 1
    if max_size >= 16:
        return "heading", 2
    if max_size >= 14.5:
        return "heading", 3
    if max_size >= 13:
        return "heading", 4
    if max_size >= 11:
        return "heading", 5
    return "heading", 5


def _is_page_artifact(text: str, page_number: Any) -> bool:
    """Return true for repeated PDF header/footer text."""

    if text == "System Reference Document 5.2.1":
        return True
    return isinstance(page_number, int) and text == str(page_number)


def _join_lines(parts: list[str]) -> str:
    text = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if text.endswith(("\u00ad", "-")):
            text = text[:-1] + part
        elif text:
            text += f" {part}"
        else:
            text = part
    return text


def _union_bbox(lines: list[dict[str, Any]]) -> list[float]:
    boxes = [line.get("bbox", []) for line in lines]
    boxes = [box for box in boxes if isinstance(box, list) and len(box) == 4]
    if not boxes:
        return []
    return [
        min(float(box[0]) for box in boxes),
        min(float(box[1]) for box in boxes),
        max(float(box[2]) for box in boxes),
        max(float(box[3]) for box in boxes),
    ]


def _bbox_center_inside(bbox: Any, regions: list[list[float]]) -> bool:
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    center_x = (float(bbox[0]) + float(bbox[2])) / 2
    center_y = (float(bbox[1]) + float(bbox[3])) / 2
    return any(
        region[0] <= center_x <= region[2] and region[1] <= center_y <= region[3]
        for region in regions
        if len(region) == 4
    )


def _line_groups(
    block: dict[str, Any],
    page_number: Any,
    excluded_regions: list[list[float]],
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for line_index, line in enumerate(block.get("lines", [])):
        if _bbox_center_inside(line.get("bbox"), excluded_regions):
            continue
        spans = line.get("spans", [])
        text = "".join(str(span.get("text", "")) for span in spans).strip()
        if not text or _is_page_artifact(text, page_number):
            continue
        role, heading_level = _classify_paragraph(spans)
        first_span = spans[0] if spans else {}
        first_font = str(first_span.get("font", ""))
        starts_metadata_label = (
            str(first_span.get("text", "")).strip().endswith(":")
            and any(weight in first_font for weight in ("SemiBold", "Semibold", "Bold"))
        )
        can_extend = (
            role == "body"
            and not starts_metadata_label
            and groups
            and groups[-1]["role"] == role
            and groups[-1]["heading_level"] == heading_level
        )
        if can_extend:
            groups[-1]["lines"].append(line)
            groups[-1]["line_indexes"].append(line_index)
        else:
            groups.append(
                {
                    "role": role,
                    "heading_level": heading_level,
                    "lines": [line],
                    "line_indexes": [line_index],
                }
            )
    return groups


def _is_spanning(node: dict[str, Any], page_width: float) -> bool:
    bbox = node.get("bbox", [])
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    return float(bbox[2]) - float(bbox[0]) >= page_width * 0.6


def _reading_order_key(
    node: dict[str, Any],
    page_width: float,
    spanning_y: list[float],
) -> tuple[int, int, float, float]:
    bbox = node.get("bbox", [])
    if not isinstance(bbox, list) or len(bbox) != 4:
        return (0, 0, 0.0, 0.0)
    y = float(bbox[1])
    band = sum(boundary <= y for boundary in spanning_y)
    if _is_spanning(node, page_width):
        return (band, -1, y, float(bbox[0]))
    center = (float(bbox[0]) + float(bbox[2])) / 2
    column = 0 if center < page_width / 2 else 1
    return (band, column, y, float(bbox[0]))


def _assign_heading_paths(pages: list[dict[str, Any]]) -> None:
    stack: list[tuple[int, str]] = []
    for page in pages:
        for node in page.get("nodes", []):
            if node.get("type") == "heading":
                level = int(node.get("heading_level") or 6)
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, str(node.get("text", ""))))
            node["heading_path"] = [title for _, title in stack]


def normalize_extracted(extracted: dict[str, Any]) -> dict[str, Any]:
    """Build ordered structural nodes while retaining source layout evidence."""

    pages = []
    for page in extracted.get("pages", []):
        page_number = page.get("page_number")
        page_width = float(page.get("width") or 0)
        nodes: list[dict[str, Any]] = []
        table_regions = [
            [float(value) for value in table.get("bbox", [])]
            for table in page.get("tables", [])
            if len(table.get("bbox", [])) == 4
        ]
        for fallback_block_index, block in enumerate(page.get("blocks", [])):
            block_index = int(block.get("block_index", fallback_block_index))
            for group in _line_groups(block, page_number, table_regions):
                lines = group["lines"]
                line_indexes = group["line_indexes"]
                spans = [span for line in lines for span in line.get("spans", [])]
                line_texts = [
                    "".join(str(span.get("text", "")) for span in line.get("spans", []))
                    for line in lines
                ]
                words = [
                    word
                    for word in page.get("words", [])
                    if word.get("block_index") == block_index
                    and word.get("line_index") in line_indexes
                ]
                nodes.append(
                    {
                        "type": "heading" if group["role"] == "heading" else "paragraph",
                        "text": _join_lines(line_texts),
                        "heading_level": group["heading_level"],
                        "page_number": page_number,
                        "bbox": _union_bbox(lines),
                        "source_block_index": block_index,
                        "source_line_indexes": line_indexes,
                        "spans": spans,
                        "words": words,
                    }
                )

        for table_index, table in enumerate(page.get("tables", [])):
            nodes.append(
                {
                    "type": "table",
                    "page_number": page_number,
                    "bbox": table.get("bbox", []),
                    "source_table_index": table_index,
                    "rows": table.get("rows", []),
                }
            )

        spanning_y = sorted(
            float(node["bbox"][1])
            for node in nodes
            if _is_spanning(node, page_width)
        )
        nodes.sort(
            key=lambda node: _reading_order_key(node, page_width, spanning_y)
        )
        for node_index, node in enumerate(nodes, start=1):
            node["id"] = f"p{int(page_number):04d}-n{node_index:04d}"
        pages.append(
            {
                "page_number": page.get("page_number"),
                "width": page.get("width"),
                "height": page.get("height"),
                "nodes": nodes,
            }
        )

    _assign_heading_paths(pages)

    return {
        "schema_version": "2.0.0",
        "stage": "normalized",
        "source": extracted.get("source", {}),
        "pages": pages,
    }
