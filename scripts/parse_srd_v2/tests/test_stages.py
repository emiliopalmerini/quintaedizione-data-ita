from __future__ import annotations

from pathlib import Path

from scripts.parse_srd_v2 import stages
from scripts.parse_srd_v2.manifest import read_json, write_json
from scripts.parse_srd_v2.stages import ensure_output_tree, run_normalize, run_parse, run_validate


def test_ensure_output_tree_creates_contracted_directories(tmp_path: Path) -> None:
    paths = ensure_output_tree(tmp_path)

    assert sorted(paths) == ["extracted", "normalized", "reports", "sections", "v2"]
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
    assert len(document["pages"][0]["nodes"]) == 1
    assert document["pages"][0]["nodes"][0]["text"] == "Incantesimi"


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
                    "nodes": [
                        {"text": "Origini dei personaggi", "type": "heading", "page_number": 93},
                        {"text": "Soldato", "type": "heading", "page_number": 93},
                        {"text": "Punteggi di caratteristica: Forza, Destrezza, Costituzione", "type": "paragraph", "page_number": 93},
                        {"text": "Talento: Selvaggio Attaccante", "type": "paragraph", "page_number": 93},
                        {"text": "Competenze nelle abilit\u00e0: Atletica e Intimidire", "type": "paragraph", "page_number": 93},
                        {"text": "Competenza negli strumenti: Strumenti da gioco", "type": "paragraph", "page_number": 93},
                        {"text": "Equipaggiamento: Lancia, abito comune", "type": "paragraph", "page_number": 93},
                        {"text": "Hai servito in una compagnia militare.", "type": "paragraph", "page_number": 94},
                        {"text": "Specie dei personaggi", "type": "heading", "page_number": 94},
                        {"text": "Dragonide", "type": "heading", "page_number": 94},
                        {"text": "Tipo di creatura: umanoide", "type": "paragraph", "page_number": 94},
                        {"text": "Taglia: Media", "type": "paragraph", "page_number": 94},
                        {"text": "Velocit\u00e0: 9 metri", "type": "paragraph", "page_number": 94},
                    ],
                },
                {
                    "page_number": 98,
                    "nodes": [
                        {"text": "Talenti", "type": "heading", "page_number": 98},
                        {"text": "Talenti Origini", "type": "heading", "page_number": 98},
                        {"text": "Abile", "type": "heading", "page_number": 98},
                        {"text": "Talento Origini", "type": "paragraph", "page_number": 98},
                        {"text": "Il personaggio ottiene competenza.", "type": "paragraph", "page_number": 98},
                    ],
                }
            ],
        },
    )

    report_path = run_parse(normalized_dir, tmp_path / "out")
    report = read_json(report_path)
    sections = read_json(tmp_path / "out" / "sections" / "sections.json")
    origin_envelope = read_json(tmp_path / "out" / "v2" / "origini.json")
    species_envelope = read_json(tmp_path / "out" / "v2" / "specie.json")
    talent_envelope = read_json(tmp_path / "out" / "v2" / "talenti.json")
    coverage = read_json(tmp_path / "out" / "reports" / "coverage.json")
    summary = read_json(tmp_path / "out" / "reports" / "summary.json")

    assert report["errors"] == []
    assert report["collection_item_counts"] == {"origini": 1, "specie": 1, "talenti": 1}
    assert report["unsupported_section_count"] == 10
    assert sections["sections"][3]["id"] == "origini"
    assert origin_envelope["collection"] == "origini"
    assert origin_envelope["items"][0]["id"] == "soldato"
    assert species_envelope["collection"] == "specie"
    assert species_envelope["items"][0]["id"] == "dragonide"
    assert talent_envelope["collection"] == "talenti"
    assert talent_envelope["items"][0]["id"] == "abile"
    assert coverage["covered_section_count"] == 3
    assert coverage["empty_section_count"] == 10
    assert summary["status"] == "failed"
    assert summary["parse"]["collection_item_counts"] == {
        "origini": 1,
        "specie": 1,
        "talenti": 1,
    }
    assert summary["parse"]["unsupported_section_count"] == 10


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
        },
        "collection": "origini",
        "items": [
            {
                "id": "soldato",
                "name": "Soldato",
                "source_id": "srd-5.2.1-it",
                "provenance": {
                    "page_start": 93,
                    "page_end": 93,
                    "heading_path": ["Origini", "Soldato"],
                    "section_id": "origini",
                    "parser": "origini",
                },
                "ability_scores": "Forza, Destrezza, Costituzione",
                "feat": "Aggressore selvaggio",
                "skill_proficiencies": "Atletica e Intimidire",
                "tool_proficiency": "Strumenti da gioco",
                "equipment": "Lancia e abito comune",
                "description": [],
            }
        ],
    }
    path = tmp_path / "origini.json"
    write_json(path, envelope)

    report = run_validate(path)

    assert report["errors"] == []


def test_run_build_stops_after_canonical_parse(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []

    def fake_extract(_pdf_path: Path, output_dir: Path) -> Path:
        calls.append("extract")
        return output_dir / "extracted" / "pages.json"

    def fake_normalize(_extracted_dir: Path, output_dir: Path) -> Path:
        calls.append("normalize")
        return output_dir / "normalized" / "document.json"

    def fake_parse(_normalized_dir: Path, output_dir: Path) -> Path:
        calls.append("parse")
        return output_dir / "reports" / "parse.json"

    monkeypatch.setattr(stages, "run_extract", fake_extract)
    monkeypatch.setattr(stages, "run_normalize", fake_normalize)
    monkeypatch.setattr(stages, "run_parse", fake_parse)

    stages.run_build(tmp_path / "source.pdf", tmp_path / "output")

    assert calls == ["extract", "normalize", "parse"]
