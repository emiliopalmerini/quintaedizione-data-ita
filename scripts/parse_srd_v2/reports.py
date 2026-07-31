"""Structured reports for parser v2 stages."""

from __future__ import annotations

from typing import Any


def build_confidence_report(parse_report: dict[str, Any]) -> dict[str, Any]:
    """Summarize explicit ignored-node reasons and review warnings."""

    counts: dict[str, int] = {}
    for entry in parse_report.get("node_accounting", {}).get("ignored_nodes", []):
        reason = str(entry.get("reason", "unknown"))
        counts[reason] = counts.get(reason, 0) + 1
    warning_reasons = {
        reason: count
        for reason, count in counts.items()
        if reason.startswith("unsupported") or reason.startswith("unrecognized")
    }
    return {
        "schema_version": "2.0.0",
        "stage": "confidence",
        "ignored_reason_counts": dict(sorted(counts.items())),
        "warnings": [
            f"{count} nodes ignored as {reason}"
            for reason, count in sorted(warning_reasons.items())
        ],
        "warning_count": sum(warning_reasons.values()),
        "errors": [],
    }


def build_references_report(
    by_collection: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Report resolved references, editorial disagreements, and broken targets."""

    classes = by_collection.get("classi", [])
    spells = by_collection.get("incantesimi", [])
    class_pairs = {
        (str(class_item.get("id", "")), str(spell_id))
        for class_item in classes
        for spell_id in class_item.get("spell_ids", [])
    }
    subtitle_pairs = {
        (str(class_id), str(spell.get("id", "")))
        for spell in spells
        for class_id in spell.get("class_ids", [])
    }
    subtitle_only = [
        {"class_id": class_id, "spell_id": spell_id}
        for class_id, spell_id in sorted(subtitle_pairs - class_pairs)
    ]
    list_only = [
        {"class_id": class_id, "spell_id": spell_id}
        for class_id, spell_id in sorted(class_pairs - subtitle_pairs)
    ]

    glossary = by_collection.get("glossario_delle_regole", [])
    glossary_ids = {str(item.get("id", "")) for item in glossary}
    glossary_reference_count = 0
    errors: list[str] = []
    for item in glossary:
        for reference in item.get("related_entry_refs", []):
            glossary_reference_count += 1
            target_id = str(reference.get("id", ""))
            if target_id not in glossary_ids:
                errors.append(
                    "glossario_delle_regole: "
                    f"{item.get('id')} references missing entry {target_id}"
                )

    return {
        "schema_version": "2.0.0",
        "stage": "references",
        "class_spell_membership_count": len(class_pairs),
        "glossary_reference_count": glossary_reference_count,
        "subtitle_only_class_spells": subtitle_only,
        "spell_list_only_class_spells": list_only,
        "warning_count": len(subtitle_only) + len(list_only),
        "errors": errors,
    }


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
