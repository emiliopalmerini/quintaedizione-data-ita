"""Structured reports for parser v2 stages."""

from __future__ import annotations

from typing import Any


def _section_entry(section: dict[str, Any]) -> dict[str, Any]:
    node_count = int(section.get("node_count", 0))
    coverage = str(section.get("coverage", "empty"))
    page_numbers = sorted(
        {
            node.get("page_number")
            for node in section.get("nodes", [])
            if isinstance(node.get("page_number"), int)
        }
    )

    return {
        "section_id": section.get("id"),
        "title": section.get("title"),
        "page_start": section.get("page_start"),
        "page_end": section.get("page_end"),
        "heading_path": section.get("heading_path", []),
        "parser": section.get("parser"),
        "collection": section.get("collection"),
        "coverage": coverage,
        "node_count": node_count,
        "page_numbers": page_numbers,
    }


def build_coverage_report(sections_artifact: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic required-section coverage report."""

    sections = [_section_entry(section) for section in sections_artifact.get("sections", [])]
    empty_sections = [
        str(section["section_id"])
        for section in sections
        if section["coverage"] != "covered" or section["node_count"] <= 0
    ]

    return {
        "schema_version": "2.0.0",
        "stage": "coverage",
        "source": sections_artifact.get("source", {}),
        "section_count": len(sections),
        "covered_section_count": len(sections) - len(empty_sections),
        "empty_section_count": len(empty_sections),
        "sections": sections,
        "errors": [
            f"required section has no normalized nodes: {section_id}"
            for section_id in empty_sections
        ],
    }


def build_summary_report(
    sections_artifact: dict[str, Any],
    parse_report: dict[str, Any],
    coverage_report: dict[str, Any],
) -> dict[str, Any]:
    """Build a concise run summary from parse and coverage diagnostics."""

    collection_item_counts: dict[str, int] = {}
    for collection in parse_report.get("collections", []):
        collection_id = str(collection.get("collection", ""))
        if not collection_id:
            continue
        collection_item_counts[collection_id] = collection_item_counts.get(collection_id, 0) + int(
            collection.get("item_count", 0)
        )

    parse_errors = [str(error) for error in parse_report.get("errors", [])]
    coverage_errors = [str(error) for error in coverage_report.get("errors", [])]
    unsupported_sections = parse_report.get("unsupported_sections", [])
    node_accounting = parse_report.get("node_accounting", {})

    if parse_errors or coverage_errors:
        status = "failed"
    elif unsupported_sections:
        status = "partial"
    else:
        status = "ok"

    return {
        "schema_version": "2.0.0",
        "stage": "summary",
        "status": status,
        "source": sections_artifact.get("source", {}),
        "coverage": {
            "section_count": coverage_report.get("section_count", 0),
            "covered_section_count": coverage_report.get("covered_section_count", 0),
            "empty_section_count": coverage_report.get("empty_section_count", 0),
        },
        "parse": {
            "collection_item_counts": collection_item_counts,
            "unsupported_section_count": len(unsupported_sections),
            "error_count": len(parse_errors),
        },
        "node_accounting": {
            "consumed_node_count": node_accounting.get("consumed_node_count", 0),
            "ignored_node_count": node_accounting.get("ignored_node_count", 0),
            "unassigned_node_count": node_accounting.get("unassigned_node_count", 0),
            "missing_node_id_count": node_accounting.get("missing_node_id_count", 0),
        },
        "errors": coverage_errors + parse_errors,
    }
