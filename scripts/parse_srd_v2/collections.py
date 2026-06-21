"""Canonical v2 collection registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CollectionSpec:
    """One canonical v2 collection and its legacy compatibility output."""

    id: str
    display_label: str
    compatibility_output: str
    notes: str


COLLECTIONS: tuple[CollectionSpec, ...] = (
    CollectionSpec("incantesimi", "Incantesimi", "spells.json", "Spell entities."),
    CollectionSpec(
        "mostri",
        "Mostri",
        "monsters.json",
        "Monster stat blocks from the Mostri source section.",
    ),
    CollectionSpec(
        "animali",
        "Animali",
        "monsters.json",
        "Animal stat blocks from the Animali source section.",
    ),
    CollectionSpec("classi", "Classi", "classes.json", "Player classes and subclasses."),
    CollectionSpec(
        "origini",
        "Origini",
        "backgrounds.json",
        "Character origins; legacy compatibility output remains backgrounds.json.",
    ),
    CollectionSpec("specie", "Specie", "species.json", "Playable species."),
    CollectionSpec("talenti", "Talenti", "feats.json", "Feat entities."),
    CollectionSpec(
        "equipaggiamento",
        "Equipaggiamento",
        "equipment.json",
        "Equipment domain, including armi, armature, strumenti, servizi, cavalcature, and veicoli.",
    ),
    CollectionSpec(
        "oggetti_magici",
        "Oggetti Magici",
        "magic_items.json",
        "Magic item entities.",
    ),
    CollectionSpec(
        "regole",
        "Regole",
        "rules_*.json",
        "Rule entries from gameplay, character creation, and game tools.",
    ),
    CollectionSpec(
        "glossario_delle_regole",
        "Glossario delle regole",
        "glossary.json",
        "Glossary entries from the SRD rules glossary.",
    ),
)

_BY_ID = {spec.id: spec for spec in COLLECTIONS}


def collection_ids() -> list[str]:
    """Return canonical v2 collection IDs in deterministic order."""

    return [spec.id for spec in COLLECTIONS]


def get_collection(collection_id: str) -> CollectionSpec:
    """Return one collection spec or raise ``KeyError``."""

    return _BY_ID[collection_id]
