from __future__ import annotations

from scripts.parse_srd_v2.manifest import GeneratedMetadata, SourceMetadata
from scripts.parse_srd_v2.schema import empty_envelope, validate_envelope


def _source() -> SourceMetadata:
    return SourceMetadata(
        id="srd-5.2.1-it",
        title="System Reference Document 5.2.1 Italiano",
        checksum_sha256="abc",
        page_count=405,
        profile="srd-5.2.1-it",
    )


def _generated() -> GeneratedMetadata:
    return GeneratedMetadata(
        parser="parse_srd_v2",
        parser_version="test",
    )


def test_empty_envelope_uses_canonical_collection_id() -> None:
    envelope = empty_envelope("incantesimi", source=_source(), generated=_generated())

    assert envelope["schema_version"] == "2.0.0"
    assert envelope["collection"] == "incantesimi"
    assert envelope["items"] == []
    assert validate_envelope(envelope) == []


def test_validate_envelope_rejects_duplicate_item_ids() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["items"] = [
        {"id": "soldato", "source_id": "srd-5.2.1-it", "provenance": {}},
        {"id": "soldato", "source_id": "srd-5.2.1-it", "provenance": {}},
    ]

    assert "duplicate item id: soldato" in validate_envelope(envelope)


def test_validate_envelope_rejects_unknown_collection() -> None:
    envelope = empty_envelope("incantesimi", source=_source(), generated=_generated())
    envelope["collection"] = "spells"

    assert "unknown collection: spells" in validate_envelope(envelope)


def test_validate_envelope_rejects_incomplete_entity_contract() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "Soldato",
            "source_id": "another-source",
            "provenance": {},
            "unknown": True,
        }
    ]

    errors = validate_envelope(envelope)

    assert "items[0].id must be a lowercase ASCII slug" in errors
    assert "items[0].name is required" in errors
    assert "items[0].source_id must match source.id" in errors
    assert "items[0].provenance.page_start is required" in errors
    assert "items[0].provenance.page_end is required" in errors
    assert "items[0].provenance.heading_path is required" in errors
    assert "items[0].provenance.section_id is required" in errors
    assert "items[0].provenance.parser is required" in errors
    assert "items[0] has unknown fields: unknown" in errors


def test_validate_envelope_rejects_unknown_envelope_fields() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["generated_at"] = "2026-01-01T00:00:00Z"

    assert "envelope has unknown fields: generated_at" in validate_envelope(envelope)


def test_validate_envelope_rejects_invalid_collection_field_types() -> None:
    envelope = empty_envelope("origini", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "soldato",
            "name": "Soldato",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": "93",
                "page_end": 92,
                "heading_path": [],
                "section_id": "",
                "parser": "origini",
            },
            "ability_scores": [],
            "feat": "Aggressore selvaggio",
            "skill_proficiencies": "Atletica e Intimidire",
            "tool_proficiency": "Strumenti da gioco",
            "equipment": "Lancia e abito comune",
            "description": "testo",
        }
    ]

    errors = validate_envelope(envelope)

    assert "items[0].provenance.page_start must be an integer" in errors
    assert "items[0].provenance.heading_path must be a non-empty string list" in errors
    assert "items[0].provenance.section_id must be a non-empty string" in errors
    assert "items[0].ability_scores must be a non-empty string" in errors
    assert "items[0].description must be a content segment list" in errors


def test_validate_envelope_accepts_typed_weapon_equipment() -> None:
    envelope = empty_envelope(
        "equipaggiamento",
        source=_source(),
        generated=_generated(),
    )
    envelope["items"] = [
        {
            "id": "randello",
            "name": "Randello",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 101,
                "page_end": 101,
                "heading_path": ["Equipaggiamento", "Armi", "Randello"],
                "section_id": "equipaggiamento",
                "parser": "equipaggiamento",
            },
            "category_id": "arma",
            "subcategory_id": "armi-da-mischia-semplici",
            "subcategory_name": "Armi da mischia semplici",
            "cost": {"quantity": 1, "unit": "ma"},
            "weight": {"quantity": 1, "unit": "kg"},
            "damage": {"dice": "1d4", "type_id": "contundenti"},
            "property_ids": ["leggera"],
            "mastery_id": "rallentare",
            "description": [],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["weight"] = None
    assert validate_envelope(envelope) == []
    envelope["items"][0]["weight"] = {"quantity": 1, "unit": "kg"}

    envelope["items"][0]["cost"] = {"quantity": "1", "unit": "ma", "extra": True}
    errors = validate_envelope(envelope)
    assert "items[0].cost has unknown fields: extra" in errors
    assert "items[0].cost.quantity must be a number" in errors


def test_validate_envelope_accepts_non_weapon_equipment() -> None:
    envelope = empty_envelope(
        "equipaggiamento", source=_source(), generated=_generated()
    )
    envelope["items"] = [
        {
            "id": "scorte-da-alchimista",
            "name": "Scorte da alchimista",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 105,
                "page_end": 105,
                "heading_path": ["Equipaggiamento", "Strumenti", "Scorte da alchimista"],
                "section_id": "equipaggiamento",
                "parser": "equipaggiamento",
            },
            "category_id": "strumento",
            "subcategory_id": "strumenti-da-artigiano",
            "subcategory_name": "Strumenti da artigiano",
            "cost": {"quantity": 50, "unit": "mo"},
            "weight": {"quantity": 4, "unit": "kg"},
            "attributes": [
                {
                    "id": "caratteristica",
                    "name": "Caratteristica",
                    "value": "Intelligenza",
                }
            ],
            "description": [],
        }
    ]

    assert validate_envelope(envelope) == []


def test_validate_envelope_accepts_typed_spell() -> None:
    envelope = empty_envelope("incantesimi", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "allarme",
            "name": "Allarme",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 140,
                "page_end": 140,
                "heading_path": ["Incantesimi", "Descrizioni", "Allarme"],
                "section_id": "incantesimi",
                "parser": "incantesimi",
            },
            "level": 1,
            "school_id": "abiurazione",
            "class_ids": ["mago", "ranger"],
            "casting_time": "1 minuto o rituale",
            "range": "9 metri",
            "components": {
                "verbal": True,
                "somatic": True,
                "material": True,
                "material_text": "una campanella",
            },
            "duration": "8 ore",
            "ritual": True,
            "concentration": False,
            "description": [{"type": "text", "text": "Descrizione."}],
            "at_higher_levels": [],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["class_ids"] = ["Mago"]
    assert (
        "items[0].class_ids must be a lowercase ASCII slug list"
        in validate_envelope(envelope)
    )


def test_validate_envelope_accepts_class_progression() -> None:
    envelope = empty_envelope("classi", source=_source(), generated=_generated())
    provenance = {
        "page_start": 33,
        "page_end": 35,
        "heading_path": ["Classi", "Barbaro"],
        "section_id": "classi",
        "parser": "classi",
    }
    envelope["items"] = [
        {
            "id": "barbaro",
            "name": "Barbaro",
            "source_id": "srd-5.2.1-it",
            "provenance": provenance,
            "hit_die": 12,
            "progression": [
                {
                    "level": 1,
                    "proficiency_bonus": 2,
                    "feature_ids": ["barbaro-ira"],
                    "resources": [{"id": "ira", "value": "2"}],
                }
            ],
            "features": [
                {
                    "id": "barbaro-ira",
                    "name": "Ira",
                    "level": 1,
                    "provenance": provenance,
                    "description": [{"type": "text", "text": "Descrizione."}],
                }
            ],
            "subclasses": [],
            "spell_ids": [],
            "description": [],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["progression"][0]["feature_ids"] = ["Ira"]
    assert (
        "items[0].progression[0].feature_ids must be a lowercase ASCII slug list"
        in validate_envelope(envelope)
    )


def test_validate_envelope_accepts_flat_rule() -> None:
    envelope = empty_envelope("regole", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "come-si-gioca-prove",
            "title": "Prove",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 5,
                "page_end": 6,
                "heading_path": ["Come si gioca", "Prove"],
                "section_id": "come_si_gioca",
                "parser": "regole",
            },
            "parent_id": "come-si-gioca",
            "depth": 2,
            "order": 0,
            "content": [{"type": "text", "text": "Una prova."}],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["parent_id"] = "Come si gioca"
    assert (
        "items[0].parent_id must be null or a lowercase ASCII slug"
        in validate_envelope(envelope)
    )


def test_validate_envelope_accepts_magic_item() -> None:
    envelope = empty_envelope("oggetti_magici", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "ali-del-volo",
            "name": "Ali del volo",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 237,
                "page_end": 237,
                "heading_path": ["Oggetti magici", "Oggetti magici A–Z", "Ali del volo"],
                "section_id": "oggetti_magici",
                "parser": "oggetti_magici",
            },
            "type_id": "oggetto-meraviglioso",
            "type_name": "Oggetto meraviglioso",
            "rarity_id": "raro",
            "attunement": {"required": True, "requirement_text": ""},
            "description": [{"type": "text", "text": "Descrizione."}],
        }
    ]

    assert validate_envelope(envelope) == []


def test_validate_envelope_accepts_creature_stat_block() -> None:
    envelope = empty_envelope("mostri", source=_source(), generated=_generated())
    envelope["items"] = [
        {
            "id": "aboleth",
            "name": "Aboleth",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 294,
                "page_end": 294,
                "heading_path": ["Mostri A-Z", "Aboleth"],
                "section_id": "mostri",
                "parser": "mostri",
            },
            "collection_id": "mostri",
            "group": "Mostri A-Z",
            "creature_type_id": "aberrazione",
            "size_id": "grande",
            "alignment": "legale malvagio",
            "ac": 17,
            "initiative": "+7 (17)",
            "hp": {"average": 150, "formula": "20d10 + 40"},
            "speed": "3 m, nuoto 12 m",
            "ability_scores": {
                "for": 21,
                "des": 9,
                "cos": 15,
                "int": 18,
                "sag": 15,
                "car": 18,
            },
            "ability_modifiers": {
                "for": 5,
                "des": -1,
                "cos": 2,
                "int": 4,
                "sag": 2,
                "car": 4,
            },
            "saving_throw_bonuses": {
                "for": 5,
                "des": 3,
                "cos": 6,
                "int": 8,
                "sag": 6,
                "car": 4,
            },
            "skills": "Percezione +10",
            "vulnerabilities": "",
            "resistances": "freddo",
            "immunities": "",
            "equipment": "",
            "senses": "Percezione passiva 20",
            "languages": "telepatia 36 m",
            "challenge_rating": "10",
            "experience_points": 5900,
            "lair_experience_points": None,
            "proficiency_bonus": 4,
            "classification_details": "",
            "alternate_size_id": None,
            "traits": [
                {
                    "id": "anfibio",
                    "name": "Anfibio",
                    "description": [
                        {"type": "text", "text": "Respira in aria e acqua."}
                    ],
                }
            ],
            "actions": [],
            "bonus_actions": [],
            "reactions": [],
            "legendary_actions": [],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["collection_id"] = "animali"
    assert (
        "items[0].collection_id must match envelope collection"
        in validate_envelope(envelope)
    )


def test_validate_envelope_accepts_glossary_entry() -> None:
    envelope = empty_envelope(
        "glossario_delle_regole", source=_source(), generated=_generated()
    )
    envelope["items"] = [
        {
            "id": "accecato-condizione",
            "term": "Accecato [condizione]",
            "source_id": "srd-5.2.1-it",
            "provenance": {
                "page_start": 202,
                "page_end": 202,
                "heading_path": ["Glossario delle regole", "Accecato [condizione]"],
                "section_id": "glossario_delle_regole",
                "parser": "glossario_delle_regole",
            },
            "descriptor_id": "condizione",
            "content": [{"type": "text", "text": "Il personaggio non vede."}],
            "related_entry_refs": [
                {
                    "source_id": "srd-5.2.1-it",
                    "collection": "glossario_delle_regole",
                    "id": "accecato-condizione",
                    "text": "Accecato",
                }
            ],
        }
    ]

    assert validate_envelope(envelope) == []

    envelope["items"][0]["related_entry_refs"][0]["id"] = "termine-mancante"
    assert (
        "items[0].related_entry_refs[0].id references missing glossary entry: termine-mancante"
        in validate_envelope(envelope)
    )
