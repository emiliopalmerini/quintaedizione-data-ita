from __future__ import annotations

from pathlib import Path

from scripts.parse_srd_v2.manifest import read_json, write_json
from scripts.parse_srd_v2.stages import ensure_output_tree, run_normalize, run_validate


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
    assert document["pages"][0]["paragraphs"][0]["text"] == "Incantesimi"


def test_run_validate_reports_missing_collection_envelopes(tmp_path: Path) -> None:
    v2_dir = tmp_path / "v2"
    v2_dir.mkdir()

    report = run_validate(v2_dir)

    assert "no v2 JSON files found" in report["errors"][0]
    assert any("missing collection envelope: incantesimi" == err for err in report["errors"])
