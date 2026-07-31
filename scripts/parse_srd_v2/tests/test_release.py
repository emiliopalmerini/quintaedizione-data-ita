from pathlib import Path

from scripts.parse_srd_v2.manifest import file_sha256, write_json
from scripts.parse_srd_v2.release import create_release_archive


def test_release_archive_is_deterministic_and_checksummed(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    write_json(bundle / "manifest.json", {"dataset_version": "1.0.0"})
    write_json(bundle / "v2" / "origini.json", {"items": []})

    first, first_checksum = create_release_archive(bundle, tmp_path / "first")
    second, _ = create_release_archive(bundle, tmp_path / "second")

    assert first.read_bytes() == second.read_bytes()
    assert first_checksum.read_text(encoding="ascii") == (
        f"{file_sha256(first)}  quintaedizione-data-ita-1.0.0.tar.gz\n"
    )
