from scripts.parse_srd_v2.references import resolve_class_spell_lists


def test_resolve_class_spell_lists_uses_exact_names_and_source_aliases() -> None:
    classes = [
        {
            "id": "mago",
            "_spell_names": ["Allarme", "Saltare"],
            "spell_ids": [],
        }
    ]
    spells = [
        {"id": "allarme", "name": "Allarme", "class_ids": ["mago"]},
        {"id": "salto", "name": "Salto", "class_ids": ["mago"]},
    ]

    errors = resolve_class_spell_lists(classes, spells)

    assert errors == []
    assert classes[0]["spell_ids"] == ["allarme", "salto"]
    assert "_spell_names" not in classes[0]


def test_resolve_class_spell_lists_reports_unknown_names() -> None:
    classes = [{"id": "mago", "_spell_names": ["Ignoto"], "spell_ids": []}]

    errors = resolve_class_spell_lists(classes, [])

    assert errors == ["classi: mago has unresolved spell-list entry: Ignoto"]
