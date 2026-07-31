from __future__ import annotations

from pathlib import Path

from scripts.parse_srd_v2.manifest import (
    file_sha256,
    generated_metadata,
    read_json,
    source_metadata,
    to_jsonable,
)
from scripts.parse_srd_v2.profiles import SRD_521_IT
from scripts.parse_srd_v2.stages import write_manifest


def test_file_sha256(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("abc", encoding="utf-8")

    assert file_sha256(path) == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_source_metadata_uses_profile_identity(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"fake")

    metadata = source_metadata(pdf, profile=SRD_521_IT, page_count=405)
    data = to_jsonable(metadata)

    assert data["id"] == "srd-5.2.1-it"
    assert data["title"] == "System Reference Document 5.2.1 Italiano"
    assert data["page_count"] == 405
    assert data["profile"] == "srd-5.2.1-it"


def test_generated_metadata_is_canonical() -> None:
    assert to_jsonable(generated_metadata()) == {
        "parser": "parse_srd_v2",
        "parser_version": "0.1.0",
    }


def test_manifest_contains_only_canonical_relative_paths(tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"fake")
    source = source_metadata(pdf, profile=SRD_521_IT, page_count=405)

    write_manifest(tmp_path / "output", source)
    manifest = read_json(tmp_path / "output" / "manifest.json")

    assert manifest["schema_version"] == "2.0.0"
    assert manifest["dataset_version"] == "0.1.0"
    assert manifest["locale"] == "it"
    assert "path" not in manifest["source"]
    assert manifest["collections"] == []
    assert manifest["reports"] == []
    assert manifest["paths"] == {
        "extracted": "extracted",
        "manifest": "manifest.json",
        "normalized": "normalized",
        "reports": "reports",
        "sections": "sections",
        "v2": "v2",
    }
