"""Narrow cross-collection reference resolution passes."""

from __future__ import annotations

from typing import Any


_SPELL_NAME_ALIASES = {"saltare": "salto"}


def resolve_class_spell_lists(
    classes: list[dict[str, Any]], spells: list[dict[str, Any]]
) -> list[str]:
    """Resolve source class spell-list labels to canonical spell IDs."""

    catalog = {
        str(spell.get("name", "")).casefold(): str(spell.get("id", ""))
        for spell in spells
    }
    errors: list[str] = []
    for class_item in classes:
        class_id = str(class_item.get("id", ""))
        spell_ids: list[str] = []
        for name in class_item.pop("_spell_names", []):
            key = str(name).casefold()
            key = _SPELL_NAME_ALIASES.get(key, key)
            spell_id = catalog.get(key)
            if not spell_id:
                errors.append(
                    f"classi: {class_id} has unresolved spell-list entry: {name}"
                )
                continue
            if spell_id not in spell_ids:
                spell_ids.append(spell_id)
        class_item["spell_ids"] = spell_ids
    return errors
