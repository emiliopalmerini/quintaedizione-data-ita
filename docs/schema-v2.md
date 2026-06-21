# Schema v2

Purpose: define the canonical target JSON contract.
Audience: parser implementers, data curators, and maintainers.
Status: target design.
Canonical for: generated data shape, IDs, provenance, and compatibility rules.

## File Shape

Every canonical v2 JSON file uses an envelope:

```json
{
  "schema_version": "2.0.0",
  "source": {
    "id": "srd-5.2.1-it",
    "title": "System Reference Document 5.2.1 Italiano",
    "checksum_sha256": "...",
    "page_count": 405
  },
  "generated": {
    "parser": "parse_srd_v2",
    "parser_version": "...",
    "generated_at": "..."
  },
  "collection": "incantesimi",
  "items": []
}
```

The envelope is canonical for v2. Compatibility JSON may omit the envelope when
generating the current Go-store format.

## Shared Entity Fields

Every entity in `items` has:

- `id`: deterministic stable ID.
- `name` or `title`: human display label.
- `source_id`: source edition ID, such as `srd-5.2.1-it`.
- `provenance`: source location metadata.

`provenance` includes:

- `page_start`
- `page_end`
- `heading_path`
- `section_id`
- `parser`

Coordinate anchors may be added when available:

- `bbox_page`
- `bbox`

## IDs

IDs must be deterministic, lowercase, ASCII-slug-compatible, and unique within
the source edition and collection.

Nested rules use path-aware IDs. A child rule ID must include enough parent
context to avoid colliding with another rule that has the same title.

Compatibility generation may emit legacy IDs only when they do not collide in
the legacy collection. If legacy IDs collide, the compatibility generator must
fail or apply a documented deterministic disambiguator.

## Content Segments

Rich text uses ordered content segments:

```json
[
  {"type": "text", "text": "Una creatura "},
  {"type": "condition", "id": "prono", "text": "prona"},
  {"type": "text", "text": " subisce..."}
]
```

Rules:

- `type: "text"` segments must have `text` and no required `id`.
- Reference segments must have `type`, `id`, and `text`.
- Segment order must preserve readable plain text.
- Adjacent text segments should be merged during generation.
- Broken references are validation errors.

## Collections

The v1 rebuild uses Italian canonical collection IDs. IDs are lowercase
ASCII-compatible slugs; display labels preserve the SRD nomenclature.

| v2 collection ID | Display label | Notes | Compatibility output |
| --- | --- | --- | --- |
| `incantesimi` | Incantesimi | Spell entities. | `spells.json` |
| `mostri` | Mostri | Monster stat blocks from the `Mostri` source section. | `monsters.json` |
| `animali` | Animali | Animal stat blocks from the `Animali` source section. | Merged into `monsters.json` |
| `classi` | Classi | Player classes and subclasses. | `classes.json` |
| `origini` | Origini | Character origins; replaces the legacy `backgrounds` naming used by older output. | `backgrounds.json` |
| `specie` | Specie | Playable species. | `species.json` |
| `talenti` | Talenti | Feat entities. | `feats.json` |
| `equipaggiamento` | Equipaggiamento | Equipment domain; item categories distinguish armi, armature, strumenti, servizi, cavalcature, and veicoli. | `equipment.json` |
| `oggetti_magici` | Oggetti Magici | Magic item entities. | `magic_items.json` |
| `regole` | Regole | Rule entries from `Come si gioca`, `Creazione del personaggio`, and `Strumenti di gioco`. | `rules_*.json` |
| `glossario_delle_regole` | Glossario delle regole | Glossary entries from the SRD rules glossary. | `glossary.json` |

Collection-specific fields are defined by implementation schemas, but all
collections must follow the envelope, shared entity, ID, and provenance rules.

## Compatibility Output

Compatibility JSON converts v2 data into the current Go module shape.

Compatibility generation must:

- Preserve current filenames expected by `data/srd/srd-5.5e`.
- Preserve current field names required by Go structs.
- Convert envelopes away from final compatibility files.
- Convert content segments into the current `Content` array format.
- Preserve deterministic ordering.
- Run Go store tests after generation.
