from __future__ import annotations

from pathlib import Path

from scripts.parse_srd_v2.manifest import read_json, write_json
from scripts.parse_srd_v2.stages import ensure_output_tree, run_normalize, run_parse, run_validate


def test_ensure_output_tree_creates_contracted_directories(tmp_path: Path) -> None:
    paths = ensure_output_tree(tmp_path)

    assert sorted(paths) == ["compat", "extracted", "normalized", "reports", "sections", "v2"]
    for path in paths.values():
        assert path.is_dir()


def test_run_normalize_writes_document_model(tmp_path: Path) -> None:
    extracted_dir = tmp_path / "input" / "extracted"
    write_json(
        extracted_dir / "pages.json",
        {
            "source": {"id": "srd-5.2.1-it"},
            "pages": [
                {
                    "page_number": 1,
                    "width": 595,
                    "height": 842,
                    "blocks": [
                        {
                            "lines": [
                                {
                                    "bbox": [0, 0, 1, 1],
                                    "spans": [{"text": "System Reference Document 5.2.1"}],
                                },
                                {
                                    "bbox": [0, 0, 1, 1],
                                    "spans": [{"text": "1"}],
                                },
                                {
                                    "bbox": [1, 2, 3, 4],
                                    "spans": [{"text": "  Incantesimi  "}],
                                }
                            ]
                        }
                    ],
                }
            ],
        },
    )

    out = run_normalize(extracted_dir, tmp_path / "out")
    document = read_json(out)

    assert document["stage"] == "normalized"
    assert len(document["pages"][0]["paragraphs"]) == 1
    assert document["pages"][0]["paragraphs"][0]["text"] == "Incantesimi"


def test_run_validate_reports_missing_collection_envelopes(tmp_path: Path) -> None:
    v2_dir = tmp_path / "v2"
    v2_dir.mkdir()

    report = run_validate(v2_dir)

    assert "no v2 JSON files found" in report["errors"][0]
    assert any("missing collection envelope: incantesimi" == err for err in report["errors"])


def test_run_parse_writes_sections_origini_envelope_and_report(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    write_json(
        normalized_dir / "document.json",
        {
            "schema_version": "2.0.0",
            "stage": "normalized",
            "source": {
                "id": "srd-5.2.1-it",
                "title": "System Reference Document 5.2.1 Italiano",
                "checksum_sha256": "abc",
                "page_count": 405,
            },
            "pages": [
                {
                    "page_number": 93,
                    "paragraphs": [
                        {"text": "Origini dei personaggi", "role": "heading", "page_number": 93},
                        {"text": "Soldato", "role": "heading", "page_number": 93},
                        {"text": "Punteggi di caratteristica: Forza, Destrezza, Costituzione", "role": "body", "page_number": 93},
                        {"text": "Talento: Selvaggio Attaccante", "role": "body", "page_number": 93},
                        {"text": "Competenze nelle abilit\u00e0: Atletica e Intimidire", "role": "body", "page_number": 93},
                        {"text": "Competenza negli strumenti: Strumenti da gioco", "role": "body", "page_number": 93},
                        {"text": "Equipaggiamento: Lancia, abito comune", "role": "body", "page_number": 93},
                        {"text": "Hai servito in una compagnia militare.", "role": "body", "page_number": 94},
                        {"text": "Specie dei personaggi", "role": "heading", "page_number": 94},
                        {"text": "Dragonide", "role": "heading", "page_number": 94},
                    ],
                }
            ],
        },
    )

    report_path = run_parse(normalized_dir, tmp_path / "out")
    report = read_json(report_path)
    sections = read_json(tmp_path / "out" / "sections" / "sections.json")
    envelope = read_json(tmp_path / "out" / "v2" / "origini.json")

    assert report["errors"] == []
    assert sections["sections"][3]["id"] == "origini"
    assert envelope["collection"] == "origini"
    assert envelope["items"][0]["id"] == "soldato"


def test_run_validate_accepts_single_envelope_file(tmp_path: Path) -> None:
    envelope = {
        "schema_version": "2.0.0",
        "source": {
            "id": "srd-5.2.1-it",
            "title": "System Reference Document 5.2.1 Italiano",
            "checksum_sha256": "abc",
            "page_count": 405,
        },
        "generated": {
            "parser": "parse_srd_v2",
            "parser_version": "test",
            "generated_at": "2026-01-01T00:00:00Z",
        },
        "collection": "origini",
        "items": [
            {
                "id": "soldato",
                "source_id": "srd-5.2.1-it",
                "provenance": {},
            }
        ],
    }
    path = tmp_path / "origini.json"
    write_json(path, envelope)

    report = run_validate(path)

    assert report["errors"] == []
