from __future__ import annotations

from scripts.parse_srd_v2.collections import collection_ids, get_collection


def test_collection_ids_are_italian_and_deterministic() -> None:
    assert collection_ids() == [
        "incantesimi",
        "mostri",
        "animali",
        "classi",
        "origini",
        "specie",
        "talenti",
        "equipaggiamento",
        "oggetti_magici",
        "regole",
        "glossario_delle_regole",
    ]


def test_origini_keeps_legacy_compatibility_output() -> None:
    spec = get_collection("origini")

    assert spec.display_label == "Origini"
    assert spec.compatibility_output == "backgrounds.json"
