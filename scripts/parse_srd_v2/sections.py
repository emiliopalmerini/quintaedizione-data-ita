"""Section registry and assignment for parser v2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SectionSpec:
    """One expected SRD 5.2.1 source section."""

    id: str
    title: str
    pages: tuple[int, int]
    parser: str
    collection: str


SECTIONS_521: tuple[SectionSpec, ...] = (
    SectionSpec("come_si_gioca", "Come si gioca", (5, 20), "regole", "regole"),
    SectionSpec(
        "creazione_del_personaggio",
        "Creazione del personaggio",
        (21, 31),
        "regole",
        "regole",
    ),
    SectionSpec("classi", "Classi", (32, 92), "classi", "classi"),
    SectionSpec("origini", "Origini", (93, 97), "origini", "origini"),
    SectionSpec("specie", "Specie", (93, 97), "specie", "specie"),
    SectionSpec("talenti", "Talenti", (98, 100), "talenti", "talenti"),
    SectionSpec(
        "equipaggiamento",
        "Equipaggiamento",
        (101, 117),
        "equipaggiamento",
        "equipaggiamento",
    ),
    SectionSpec("incantesimi", "Incantesimi", (118, 201), "incantesimi", "incantesimi"),
    SectionSpec(
        "glossario_delle_regole",
        "Glossario delle regole",
        (202, 219),
        "glossario_delle_regole",
        "glossario_delle_regole",
    ),
    SectionSpec("strumenti_di_gioco", "Strumenti di gioco", (220, 231), "regole", "regole"),
    SectionSpec(
        "oggetti_magici",
        "Oggetti Magici",
        (232, 288),
        "oggetti_magici",
        "oggetti_magici",
    ),
    SectionSpec("mostri", "Mostri", (289, 384), "mostri", "mostri"),
    SectionSpec("animali", "Animali", (385, 405), "animali", "animali"),
)

_BY_ID = {section.id: section for section in SECTIONS_521}


def get_section(section_id: str) -> SectionSpec:
    """Return one section spec or raise ``KeyError``."""

    return _BY_ID[section_id]


def section_ids() -> list[str]:
    """Return expected section IDs in deterministic order."""

    return [section.id for section in SECTIONS_521]


def _split_shared_origin_species_pages(
    spec: SectionSpec,
    nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Split the shared pages 93-97 into Origini and Specie sections."""

    if spec.id not in {"origini", "specie"}:
        return nodes

    species_start = None
    for index, node in enumerate(nodes):
        text = str(node.get("text", "")).strip().lower()
        if text == "specie dei personaggi":
            species_start = index
            break

    if species_start is None:
        return nodes
    if spec.id == "origini":
        return nodes[:species_start]
    return nodes[species_start:]


def assign_sections(document: dict[str, Any]) -> dict[str, Any]:
    """Assign normalized nodes to expected source sections by page range."""

    sections: list[dict[str, Any]] = []
    for spec in SECTIONS_521:
        start, end = spec.pages
        nodes: list[dict[str, Any]] = []
        for page in document.get("pages", []):
            page_number = page.get("page_number")
            if not isinstance(page_number, int) or page_number < start or page_number > end:
                continue
            nodes.extend(page.get("nodes", []))
        nodes = _split_shared_origin_species_pages(spec, nodes)

        sections.append(
            {
                "id": spec.id,
                "title": spec.title,
                "page_start": start,
                "page_end": end,
                "heading_path": [spec.title],
                "parser": spec.parser,
                "collection": spec.collection,
                "coverage": "covered" if nodes else "empty",
                "node_count": len(nodes),
                "nodes": nodes,
            }
        )

    return {
        "schema_version": "2.0.0",
        "stage": "sections",
        "source": document.get("source", {}),
        "sections": sections,
    }
