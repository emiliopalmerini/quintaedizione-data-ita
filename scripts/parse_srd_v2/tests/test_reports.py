from __future__ import annotations

from scripts.parse_srd_v2.reports import (
    build_confidence_report,
    build_coverage_report,
    build_references_report,
    build_summary_report,
)


def test_build_coverage_report_flags_empty_required_sections() -> None:
    sections_artifact = {
        "source": {"id": "srd-5.2.1-it"},
        "sections": [
            {
                "id": "origini",
                "title": "Origini",
                "page_start": 93,
                "page_end": 97,
                "heading_path": ["Origini"],
                "parser": "origini",
                "collection": "origini",
                "coverage": "covered",
                "node_count": 2,
                "nodes": [
                    {"text": "Accolito", "page_number": 93},
                    {"text": "Soldato", "page_number": 94},
                ],
            },
            {
                "id": "mostri",
                "title": "Mostri",
                "page_start": 289,
                "page_end": 384,
                "heading_path": ["Mostri"],
                "parser": "mostri",
                "collection": "mostri",
                "coverage": "empty",
                "node_count": 0,
                "nodes": [],
            },
        ],
    }

    report = build_coverage_report(sections_artifact)

    assert report["section_count"] == 2
    assert report["covered_section_count"] == 1
    assert report["empty_section_count"] == 1
    assert report["sections"][0]["page_numbers"] == [93, 94]
    assert report["errors"] == ["required section has no normalized nodes: mostri"]


def test_build_summary_report_marks_prefix_build_partial_for_unsupported_sections() -> None:
    sections_artifact = {"source": {"id": "srd-5.2.1-it"}}
    parse_report = {
        "collections": [
            {"collection": "origini", "section_id": "origini", "item_count": 4},
            {"collection": "regole", "section_id": "come_si_gioca", "item_count": 3},
        ],
        "errors": [],
        "unsupported_sections": [
            {"section_id": "classi", "parser": "classi", "collection": "classi"},
        ],
        "node_accounting": {
            "consumed_node_count": 12,
            "ignored_node_count": 2,
            "unassigned_node_count": 5,
            "missing_node_id_count": 0,
        },
    }
    coverage_report = {
        "section_count": 13,
        "covered_section_count": 13,
        "empty_section_count": 0,
        "errors": [],
    }

    report = build_summary_report(sections_artifact, parse_report, coverage_report)

    assert report["status"] == "partial"
    assert report["coverage"]["covered_section_count"] == 13
    assert report["parse"]["collection_item_counts"] == {"origini": 4, "regole": 3}
    assert report["parse"]["unsupported_section_count"] == 1
    assert report["node_accounting"] == {
        "consumed_node_count": 12,
        "ignored_node_count": 2,
        "unassigned_node_count": 5,
        "missing_node_id_count": 0,
    }
    assert report["errors"] == []


def test_build_summary_report_marks_coverage_errors_failed() -> None:
    report = build_summary_report(
        {"source": {"id": "srd-5.2.1-it"}},
        {"collections": [], "errors": [], "unsupported_sections": []},
        {
            "section_count": 13,
            "covered_section_count": 12,
            "empty_section_count": 1,
            "errors": ["required section has no normalized nodes: mostri"],
        },
    )

    assert report["status"] == "failed"
    assert report["errors"] == ["required section has no normalized nodes: mostri"]


def test_build_confidence_report_counts_ignored_reasons() -> None:
    report = build_confidence_report(
        {
            "node_accounting": {
                "ignored_nodes": [
                    {"node_id": "n1", "reason": "section_preamble"},
                    {"node_id": "n2", "reason": "unsupported_table"},
                ]
            }
        }
    )

    assert report["ignored_reason_counts"] == {
        "section_preamble": 1,
        "unsupported_table": 1,
    }
    assert report["warnings"] == ["1 nodes ignored as unsupported_table"]


def test_build_references_report_tracks_disagreements_and_broken_refs() -> None:
    report = build_references_report(
        {
            "classi": [{"id": "mago", "spell_ids": ["allarme"]}],
            "incantesimi": [
                {"id": "allarme", "class_ids": ["mago"]},
                {"id": "scudo", "class_ids": ["mago"]},
            ],
            "glossario_delle_regole": [
                {
                    "id": "azione",
                    "related_entry_refs": [{"id": "termine-mancante"}],
                }
            ],
        }
    )

    assert report["class_spell_membership_count"] == 1
    assert report["subtitle_only_class_spells"] == [
        {"class_id": "mago", "spell_id": "scudo"}
    ]
    assert report["errors"] == [
        "glossario_delle_regole: azione references missing entry termine-mancante"
    ]
