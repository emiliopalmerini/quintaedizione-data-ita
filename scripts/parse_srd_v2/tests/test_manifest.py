from __future__ import annotations

from pathlib import Path

from scripts.parse_srd_v2.manifest import file_sha256, source_metadata, to_jsonable
from scripts.parse_srd_v2.profiles import SRD_521_IT


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
