from __future__ import annotations

from pathlib import Path

import pytest

from scripts.parse_srd_v2 import stages
from scripts.parse_srd_v2.errors import BuildValidationError
from scripts.parse_srd_v2.manifest import file_sha256, read_json, write_json
from scripts.parse_srd_v2.stages import ensure_output_tree, run_normalize, run_parse, run_validate


def _with_node_ids(document: dict) -> dict:
    for page in document.get("pages", []):
        page_number = int(page["page_number"])
        for index, node in enumerate(page.get("nodes", []), start=1):
            node["id"] = f"p{page_number:04d}-n{index:04d}"
    return document


def _weapon_table_node() -> dict:
    return {
        "type": "table",
        "page_number": 101,
        "heading_path": ["Equipaggiamento", "Armi"],
        "rows": [
            {
                "cells": [
                    {"text": value}
                    for value in (
                        "Nome",
                        "Costo",
                        "Danni",
                        "Peso",
                        "Propriet\u00e0",
                        "Padronanza",
                    )
                ]
            },
            {
                "cells": [
                    {"text": value}
                    for value in (
                        "Armi da mischia semplici",
                        "",
                        "",
                        "",
                        "",
                        "",
                    )
                ]
            },
            {
                "cells": [
                    {"text": value}
                    for value in (
                        "Randello",
                        "1 MA",
                        "1d4 contundenti",
                        "1 kg",
                        "Leggera",
                        "Rallentare",
                    )
                ]
            },
        ],
    }


def _spell_nodes() -> list[dict]:
    description_path = ["Incantesimi", "Descrizioni degli incantesimi"]
    values = [
        ("heading", "Descrizioni degli incantesimi"),
        ("heading", "Allarme"),
        ("paragraph", "Abiurazione di 1\u00ba livello (Mago, Ranger)"),
        ("paragraph", "Tempo di lancio: 1 minuto o rituale"),
        ("paragraph", "Gittata: 9 metri"),
        ("paragraph", "Componenti: V, S"),
        ("paragraph", "Durata: 8 ore"),
        ("paragraph", "L'incantatore predispone un allarme."),
    ]
    nodes = []
    for index, (node_type, text) in enumerate(values):
        node = {"type": node_type, "text": text, "page_number": 140}
        if node_type == "heading":
            node["heading_level"] = 2 if index == 0 else 5
            node["heading_path"] = (
                description_path if index == 0 else [*description_path, text]
            )
        nodes.append(node)
    return nodes


def _class_nodes() -> list[dict]:
    return [
        {
            "type": "heading",
            "heading_level": 2,
            "text": "Barbaro",
            "page_number": 33,
            "heading_path": ["Classi", "Barbaro"],
        },
        {"type": "paragraph", "text": "Dado vita: d12", "page_number": 33},
        {
            "type": "table",
            "page_number": 34,
            "heading_path": ["Classi", "Barbaro"],
            "rows": [
                {
                    "cells": [
                        {"text": value}
                        for value in (
                            "Livello",
                            "Bonus di competenza",
                            "Privilegi",
                            "Ira",
                        )
                    ]
                },
                {
                    "cells": [
                        {"text": value} for value in ("1", "+2", "Ira", "2")
                    ]
                },
            ],
        },
        {
            "type": "heading",
            "heading_level": 5,
            "text": "Ira",
            "page_number": 35,
            "heading_path": ["Classi", "Barbaro", "Ira"],
        },
        {
            "type": "paragraph",
            "text": "Il barbaro combatte con furia primordiale.",
            "page_number": 35,
        },
    ]


def _rule_nodes(title: str, page_number: int) -> list[dict]:
    return [
        {
            "type": "heading",
            "heading_level": 1,
            "text": title,
            "page_number": page_number,
            "heading_path": [title],
        },
        {
            "type": "paragraph",
            "text": f"Contenuto di {title}.",
            "page_number": page_number,
        },
    ]


def _magic_item_nodes() -> list[dict]:
    root_path = ["Oggetti magici", "Oggetti magici A–Z"]
    return [
        {
            "type": "heading",
            "heading_level": 2,
            "text": "Oggetti magici A–Z",
            "page_number": 237,
            "heading_path": root_path,
        },
        {
            "type": "heading",
            "heading_level": 5,
            "text": "Ali del volo",
            "page_number": 237,
            "heading_path": [*root_path, "Ali del volo"],
        },
        {
            "type": "paragraph",
            "text": "Oggetto meraviglioso, raro (richiede sintonia)",
            "page_number": 237,
        },
        {
            "type": "paragraph",
            "text": "Il mantello si trasforma in ali.",
            "page_number": 237,
        },
    ]


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
        _with_node_ids({
            "schema_version": "2.0.0",
            "stage": "normalized",
            "source": {
                "id": "srd-5.2.1-it",
                "title": "System Reference Document 5.2.1 Italiano",
                "checksum_sha256": "abc",
                "page_count": 405,
            },
            "pages": [
                {"page_number": 5, "nodes": _rule_nodes("Come si gioca", 5)},
                {
                    "page_number": 21,
                    "nodes": _rule_nodes("Creazione del personaggio", 21),
                },
                {
                    "page_number": 33,
                    "nodes": _class_nodes(),
                },
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
                },
                {
                    "page_number": 101,
                    "nodes": [
                        {
                            "text": "Armi",
                            "type": "heading",
                            "page_number": 101,
                            "heading_path": ["Equipaggiamento", "Armi"],
                        },
                        _weapon_table_node(),
                    ],
                },
                {
                    "page_number": 140,
                    "nodes": _spell_nodes(),
                },
                {
                    "page_number": 220,
                    "nodes": _rule_nodes("Strumenti di gioco", 220),
                },
                {
                    "page_number": 237,
                    "nodes": _magic_item_nodes(),
                }
            ],
        }),
    )

    report_path = run_parse(normalized_dir, tmp_path / "out")
    report = read_json(report_path)
    sections = read_json(tmp_path / "out" / "sections" / "sections.json")
    class_envelope = read_json(tmp_path / "out" / "v2" / "classi.json")
    origin_envelope = read_json(tmp_path / "out" / "v2" / "origini.json")
    species_envelope = read_json(tmp_path / "out" / "v2" / "specie.json")
    talent_envelope = read_json(tmp_path / "out" / "v2" / "talenti.json")
    equipment_envelope = read_json(
        tmp_path / "out" / "v2" / "equipaggiamento.json"
    )
    spell_envelope = read_json(tmp_path / "out" / "v2" / "incantesimi.json")
    rules_envelope = read_json(tmp_path / "out" / "v2" / "regole.json")
    magic_item_envelope = read_json(
        tmp_path / "out" / "v2" / "oggetti_magici.json"
    )
    coverage = read_json(tmp_path / "out" / "reports" / "coverage.json")
    summary = read_json(tmp_path / "out" / "reports" / "summary.json")
    manifest = read_json(tmp_path / "out" / "manifest.json")

    assert report["errors"] == []
    assert report["collection_item_counts"] == {
        "classi": 1,
        "equipaggiamento": 1,
        "incantesimi": 1,
        "oggetti_magici": 1,
        "origini": 1,
        "regole": 3,
        "specie": 1,
        "talenti": 1,
    }
    assert report["unsupported_section_count"] == 3
    assert report["node_accounting"]["consumed_node_count"] == 36
    assert report["node_accounting"]["ignored_node_count"] == 7
    assert report["node_accounting"]["unassigned_node_count"] == 0
    assert report["node_accounting"]["missing_node_id_count"] == 0
    assert sections["sections"][3]["id"] == "origini"
    assert class_envelope["items"][0]["id"] == "barbaro"
    assert origin_envelope["collection"] == "origini"
    assert origin_envelope["items"][0]["id"] == "soldato"
    assert species_envelope["collection"] == "specie"
    assert species_envelope["items"][0]["id"] == "dragonide"
    assert talent_envelope["collection"] == "talenti"
    assert talent_envelope["items"][0]["id"] == "abile"
    assert equipment_envelope["items"][0]["id"] == "randello"
    assert spell_envelope["items"][0]["id"] == "allarme"
    assert len(rules_envelope["items"]) == 3
    assert magic_item_envelope["items"][0]["id"] == "ali-del-volo"
    assert coverage["covered_section_count"] == 10
    assert coverage["empty_section_count"] == 3
    assert summary["status"] == "failed"
    assert summary["parse"]["collection_item_counts"] == {
        "classi": 1,
        "equipaggiamento": 1,
        "incantesimi": 1,
        "oggetti_magici": 1,
        "origini": 1,
        "regole": 3,
        "specie": 1,
        "talenti": 1,
    }
    assert summary["parse"]["unsupported_section_count"] == 3
    assert manifest["collections"] == [
        {
            "collection": "classi",
            "item_count": 1,
            "path": "v2/classi.json",
            "checksum_sha256": file_sha256(
                tmp_path / "out" / "v2" / "classi.json"
            ),
        },
        {
            "collection": "equipaggiamento",
            "item_count": 1,
            "path": "v2/equipaggiamento.json",
            "checksum_sha256": file_sha256(
                tmp_path / "out" / "v2" / "equipaggiamento.json"
            ),
        },
        {
            "collection": "incantesimi",
            "item_count": 1,
            "path": "v2/incantesimi.json",
            "checksum_sha256": file_sha256(
                tmp_path / "out" / "v2" / "incantesimi.json"
            ),
        },
        {
            "collection": "oggetti_magici",
            "item_count": 1,
            "path": "v2/oggetti_magici.json",
            "checksum_sha256": file_sha256(
                tmp_path / "out" / "v2" / "oggetti_magici.json"
            ),
        },
        {
            "collection": "origini",
            "item_count": 1,
            "path": "v2/origini.json",
            "checksum_sha256": file_sha256(tmp_path / "out" / "v2" / "origini.json"),
        },
        {
            "collection": "regole",
            "item_count": 3,
            "path": "v2/regole.json",
            "checksum_sha256": file_sha256(
                tmp_path / "out" / "v2" / "regole.json"
            ),
        },
        {
            "collection": "specie",
            "item_count": 1,
            "path": "v2/specie.json",
            "checksum_sha256": file_sha256(tmp_path / "out" / "v2" / "specie.json"),
        },
        {
            "collection": "talenti",
            "item_count": 1,
            "path": "v2/talenti.json",
            "checksum_sha256": file_sha256(tmp_path / "out" / "v2" / "talenti.json"),
        },
    ]
    assert [report["path"] for report in manifest["reports"]] == [
        "reports/coverage.json",
        "reports/parse.json",
        "reports/summary.json",
    ]
    assert all(report["checksum_sha256"] for report in manifest["reports"])


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
        path = output_dir / "normalized" / "document.json"
        write_json(
            path,
            {
                "source": {
                    "id": "fixture",
                    "title": "Fixture",
                    "checksum_sha256": "abc",
                    "page_count": 1,
                    "profile": "fixture",
                }
            },
        )
        return path

    def fake_parse(_normalized_dir: Path, output_dir: Path) -> Path:
        calls.append("parse")
        write_json(output_dir / "reports" / "summary.json", {"status": "ok"})
        return output_dir / "reports" / "parse.json"

    def fake_validate(_v2_dir: Path) -> dict:
        calls.append("validate")
        return {"stage": "validate", "files": [], "errors": []}

    monkeypatch.setattr(stages, "run_extract", fake_extract)
    monkeypatch.setattr(stages, "run_normalize", fake_normalize)
    monkeypatch.setattr(stages, "run_parse", fake_parse)
    monkeypatch.setattr(stages, "run_validate", fake_validate)

    stages.run_build(tmp_path / "source.pdf", tmp_path / "output")

    assert calls == ["extract", "normalize", "parse", "validate"]
    validation = read_json(tmp_path / "output" / "reports" / "validation.json")
    assert validation["errors"] == []


def test_run_build_fails_when_validation_is_incomplete(monkeypatch, tmp_path: Path) -> None:
    output_dir = tmp_path / "output"

    monkeypatch.setattr(
        stages,
        "run_extract",
        lambda _pdf, output: output / "extracted" / "pages.json",
    )

    def fake_normalize(_extracted_dir: Path, output: Path) -> Path:
        path = output / "normalized" / "document.json"
        write_json(
            path,
            {
                "source": {
                    "id": "fixture",
                    "title": "Fixture",
                    "checksum_sha256": "abc",
                    "page_count": 1,
                    "profile": "fixture",
                }
            },
        )
        return path

    def fake_parse(_normalized_dir: Path, output: Path) -> Path:
        write_json(output / "reports" / "summary.json", {"status": "partial"})
        return output / "reports" / "parse.json"

    monkeypatch.setattr(stages, "run_normalize", fake_normalize)
    monkeypatch.setattr(stages, "run_parse", fake_parse)
    monkeypatch.setattr(
        stages,
        "run_validate",
        lambda _v2: {"stage": "validate", "files": [], "errors": ["missing classi"]},
    )

    with pytest.raises(BuildValidationError, match="partial.*missing classi"):
        stages.run_build(tmp_path / "source.pdf", output_dir)

    assert (output_dir / "reports" / "validation.json").is_file()
    assert (output_dir / "manifest.json").is_file()
