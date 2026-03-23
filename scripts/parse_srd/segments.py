"""Convert plain-text description fields to structured content segments.

Post-processing step that scans markdown strings for known entity
references (spells, damage types, conditions, etc.) and splits them
into typed segments: [{type, text, id?}, ...].
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

from .slugify import slugify


# ── Segment type ────────────────────────────────────────────────────────────


class Segment(TypedDict, total=False):
    type: str   # required
    text: str   # required
    id: str     # only for references


def _text(t: str) -> Segment:
    return Segment(type="text", text=t)


def _ref(ref_type: str, text: str, entity_id: str) -> Segment:
    return Segment(type=ref_type, text=text, id=entity_id)


# ── Fixed catalogs (Italian D&D 5e terms) ──────────────────────────────────

DAMAGE_TYPES: dict[str, str] = {
    name: slugify(name)
    for name in [
        "acido", "contundente", "freddo", "fulmine", "fuoco", "forza",
        "necrotico", "perforante", "psichico", "radioso", "tagliente",
        "tuono", "veleno",
    ]
}

CONDITIONS: dict[str, str] = {
    name: slugify(name)
    for name in [
        "accecato", "affascinato", "assordato", "avvelenato", "esausto",
        "incapacitato", "invisibile", "paralizzato", "pietrificato",
        "privo di sensi", "prono", "spaventato", "stordito",
        "trattenuto", "afferrato",
    ]
}

ABILITIES: dict[str, str] = {
    name: slugify(name)
    for name in [
        "Forza", "Destrezza", "Costituzione",
        "Intelligenza", "Saggezza", "Carisma",
    ]
}

SKILLS: dict[str, str] = {
    name: slugify(name)
    for name in [
        "Acrobazia", "Addestrare Animali", "Arcano", "Atletica",
        "Furtività", "Indagare", "Inganno", "Intimidire",
        "Intrattenere", "Intuizione", "Medicina", "Natura",
        "Percezione", "Persuasione", "Rapidità di Mano",
        "Religione", "Sopravvivenza", "Storia",
    ]
}

CREATURE_TYPES: dict[str, str] = {
    name: slugify(name)
    for name in [
        "Aberrazione", "Bestia", "Celestiale", "Costrutto",
        "Drago", "Elementale", "Fatato", "Immondo",
        "Melma", "Mostruosità", "Non morto", "Pianta",
        "Umanoide",
    ]
}


# ── Catalogs ────────────────────────────────────────────────────────────────


class Catalogs:
    """Entity catalogs for segment matching.

    Each catalog maps display name (lowercase) → entity ID.
    Entries are sorted longest-first for greedy matching.
    """

    def __init__(self) -> None:
        self._entries: dict[str, list[tuple[str, str, str]]] = {}
        self._pattern: re.Pattern[str] | None = None

    def add(self, ref_type: str, catalog: dict[str, str]) -> None:
        """Add a catalog. Keys = display names, values = entity IDs."""
        entries = [(name.lower(), name, eid) for name, eid in catalog.items()]
        entries.sort(key=lambda e: -len(e[0]))
        self._entries[ref_type] = entries
        self._pattern = None  # invalidate cached pattern

    def all_entries(self) -> list[tuple[str, str, str, str]]:
        """Return all entries as (name_lower, display_name, id, ref_type), longest first."""
        result: list[tuple[str, str, str, str]] = []
        for ref_type, entries in self._entries.items():
            for name_lower, display, eid in entries:
                result.append((name_lower, display, eid, ref_type))
        result.sort(key=lambda e: -len(e[0]))
        return result

    def pattern(self) -> re.Pattern[str] | None:
        """Compiled regex matching any catalog entry at word boundaries."""
        if self._pattern is not None:
            return self._pattern

        entries = self.all_entries()
        if not entries:
            return None

        alternatives = [re.escape(e[0]) for e in entries]
        wb_left = r"(?<![a-zA-ZÀ-ÿ])"
        wb_right = r"(?![a-zA-ZÀ-ÿ])"
        pattern_str = wb_left + "(" + "|".join(alternatives) + ")" + wb_right
        self._pattern = re.compile(pattern_str, re.IGNORECASE)
        return self._pattern

    def lookup(self, matched_text: str) -> Segment | None:
        """Find the catalog entry for a matched text."""
        lower = matched_text.lower()
        for name_lower, _, eid, ref_type in self.all_entries():
            if lower == name_lower:
                return _ref(ref_type, matched_text, eid)
        return None


def build_catalogs(outputs: dict[str, list[Any]]) -> Catalogs:
    """Build catalogs from parsed output + fixed lists."""
    cats = Catalogs()

    cats.add("damage_type", DAMAGE_TYPES)
    cats.add("condition", CONDITIONS)
    cats.add("ability", ABILITIES)
    cats.add("skill", SKILLS)
    cats.add("creature_type", CREATURE_TYPES)

    # Dynamic: spells
    spells: dict[str, str] = {}
    for entry in outputs.get("spells.json", []):
        spells[entry["name"]] = entry["id"]
    if spells:
        cats.add("spell", spells)

    # Dynamic: equipment
    equipment: dict[str, str] = {}
    for entry in outputs.get("equipment.json", []):
        equipment[entry["name"]] = entry["id"]
    if equipment:
        cats.add("equipment", equipment)

    return cats


# ── Text → Segments conversion ──────────────────────────────────────────────


def text_to_segments(text: str, catalogs: Catalogs) -> list[Segment]:
    """Convert a plain text string to a list of content segments."""
    if not text:
        return []

    pattern = catalogs.pattern()
    if pattern is None:
        return [_text(text)]

    segments: list[Segment] = []
    last_end = 0

    for m in pattern.finditer(text):
        start, end = m.start(), m.end()
        ref = catalogs.lookup(m.group(0))
        if ref is None:
            continue

        if start > last_end:
            segments.append(_text(text[last_end:start]))

        segments.append(ref)
        last_end = end

    if last_end < len(text):
        segments.append(_text(text[last_end:]))

    return segments if segments else [_text(text)]


# ── Post-processing: walk output dicts ──────────────────────────────────────

_ALL_CONTENT_FIELDS = {
    "description", "at_higher_levels", "benefit", "prerequisite",
    "content", "definition", "resistances", "damage_immunities",
    "condition_immunities",
}


def segmentize_dict(d: dict[str, Any], catalogs: Catalogs) -> None:
    """Recursively convert string fields to segments in a dict."""
    for key, value in list(d.items()):
        if key in _ALL_CONTENT_FIELDS and isinstance(value, str):
            d[key] = text_to_segments(value, catalogs)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    segmentize_dict(item, catalogs)
        elif isinstance(value, dict):
            segmentize_dict(value, catalogs)


def segmentize_outputs(outputs: dict[str, list[Any]], catalogs: Catalogs) -> None:
    """Apply segment conversion to all parsed outputs in place."""
    for entries in outputs.values():
        for entry in entries:
            if isinstance(entry, dict):
                segmentize_dict(entry, catalogs)
