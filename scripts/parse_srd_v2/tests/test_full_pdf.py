from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import pytest

from scripts.parse_srd_v2.manifest import file_sha256, read_json
from scripts.parse_srd_v2.stages import run_build


pytestmark = pytest.mark.full_pdf

_BASELINE = Path(__file__).parent / "baselines" / "srd-5.2.1-it.json"


def _source_pdf() -> Path:
    value = os.environ.get("SRD_521_IT_PDF")
    if not value:
        pytest.skip("SRD_521_IT_PDF is required for full-PDF acceptance")
    assert value is not None
    return Path(value)


def test_real_pdf_matches_release_baseline_and_rebuilds_deterministically(
    tmp_path: Path,
) -> None:
    pdf_path = _source_pdf()
    baseline = read_json(_BASELINE)
    assert file_sha256(pdf_path) == baseline["checksum_sha256"]

    first = tmp_path / "first"
    second = tmp_path / "second"
    run_build(pdf_path, first)
    run_build(pdf_path, second)

    summary = read_json(first / "reports" / "summary.json")
    assert summary["status"] == "ok"
    assert summary["errors"] == []
    assert summary["parse"]["collection_item_counts"] == baseline[
        "collection_item_counts"
    ]

    equipment = read_json(first / "v2" / "equipaggiamento.json")["items"]
    assert Counter(item["category_id"] for item in equipment) == baseline[
        "equipment_category_counts"
    ]

    classes = read_json(first / "v2" / "classi.json")["items"]
    class_semantics = baseline["class_semantics"]
    assert sum(len(item["progression"]) for item in classes) == class_semantics[
        "progression_rows"
    ]
    assert sum(len(item["subclasses"]) for item in classes) == class_semantics[
        "subclasses"
    ]
    assert sum(
        len(subclass["features"])
        for item in classes
        for subclass in item["subclasses"]
    ) == class_semantics["subclass_features"]
    assert sum(len(item["spell_ids"]) for item in classes) == class_semantics[
        "spell_memberships"
    ]

    creatures = [
        *read_json(first / "v2" / "mostri.json")["items"],
        *read_json(first / "v2" / "animali.json")["items"],
    ]
    creature_counts = baseline["creature_field_counts"]
    for field in ("vulnerabilities", "resistances", "immunities", "equipment"):
        assert sum(bool(item[field]) for item in creatures) == creature_counts[field]
    assert sum(
        item["lair_experience_points"] is not None for item in creatures
    ) == creature_counts["lair_experience_points"]
    assert sum(
        len(item["saving_throw_bonuses"]) == 6 for item in creatures
    ) == creature_counts["saving_throw_bonuses"]

    first_files = sorted(path.relative_to(first) for path in first.rglob("*.json"))
    second_files = sorted(path.relative_to(second) for path in second.rglob("*.json"))
    assert first_files == second_files
    for relative_path in first_files:
        assert file_sha256(first / relative_path) == file_sha256(second / relative_path)
