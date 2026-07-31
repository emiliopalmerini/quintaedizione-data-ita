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
    "parser_version": "..."
  },
  "collection": "incantesimi",
  "items": []
}
```

The envelope is canonical for v2. Collection files are independently usable but
are published together through the bundle manifest.

Unknown envelope and entity fields are validation errors. Collection-specific
schemas define required fields, value types, controlled vocabulary references,
and whether empty values are permitted.

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

References use the target collection and ID. Cross-source references additionally
include `source_id`; unqualified cross-source resolution is not permitted.

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

| v2 collection ID | Display label | Notes |
| --- | --- | --- |
| `incantesimi` | Incantesimi | Spell entities. |
| `mostri` | Mostri | Monster stat blocks from the `Mostri` source section. |
| `animali` | Animali | Animal stat blocks from the `Animali` source section. |
| `classi` | Classi | Classes, subclasses, features, and level progression. |
| `origini` | Origini | Character origins, proficiencies, and equipment choices. |
| `specie` | Specie | Playable species and structured traits. |
| `talenti` | Talenti | Feats with structured categories and prerequisites. |
| `equipaggiamento` | Equipaggiamento | Equipment with category-specific fields for weapons, armor, tools, services, mounts, and vehicles. |
| `oggetti_magici` | Oggetti Magici | Magic item entities. |
| `regole` | Regole | Addressable rule records with parent IDs and source order. |
| `glossario_delle_regole` | Glossario delle regole | Glossary entries and explicit related-entry references. |

Collection-specific fields are defined by implementation schemas, but all
collections must follow the envelope, shared entity, ID, and provenance rules.

## Bundle Manifest

The root manifest includes:

- `schema_version` and `dataset_version`;
- locale and source identity, checksum, title, and page count;
- parser name and version;
- one entry per collection with relative path, SHA-256 checksum, and item count;
- relative paths and checksums for required quality reports.

Canonical manifests and collection envelopes exclude wall-clock timestamps and
absolute filesystem paths so equivalent builds are byte-for-byte reproducible.

## Structured Builder Data

Collection schemas must expose values needed for builder logic without requiring
consumers to parse prose. This includes class levels and features, spell lists,
origin equipment alternatives, feat prerequisites, species choices, equipment
statistics, monster actions and spellcasting, and rule hierarchy.

Choice and prerequisite expressions use a shared recursive representation with
explicit `all`, `any`, `one_of`, `reference`, and scalar requirement nodes.
Display text may accompany the expression but cannot be its only representation.

### Equipment

Every equipment record has `category_id` and category-specific typed fields.
Weapon records include:

- `subcategory_id` and `subcategory_name`;
- `cost` as `{quantity, unit}`;
- `weight` as `{quantity, unit}`;
- `damage` as `{dice, type_id}`;
- `property_ids` in source order;
- optional `mastery_id`;
- rich-text `description`.

The parser preserves display labels where controlled IDs normalize spelling or
grammar. It must not publish an arbitrary string-to-string property map as the
canonical representation.

### Table Nodes

Normalized table nodes preserve the table bounding box, source page, ordered
rows, and ordered cells. Every cell contains text and its source bounding box.
Header and subcategory rows remain explicit rows until a typed collection parser
consumes them. Table content is not converted to markdown and is not also emitted
as duplicate paragraph nodes.

### Spells

Spell records include `level`, `school_id`, and `class_ids` as typed builder
fields. Casting time, range, and duration retain normalized display text until
their complete SRD expression grammar is implemented. Components use an object
with `verbal`, `somatic`, and `material` booleans plus optional `material_text`.
`ritual` and `concentration` are explicit booleans.

Spell entries are discovered from level-5 headings beneath the structural
`Descrizioni degli incantesimi` heading path, never from a hard-coded spell-name
inventory. `description` and `at_higher_levels` are separate content segment
lists. Spell-list tables are separate structured inputs that later resolve class
spell-list references; they are not spell definitions.

### Classes

Class records contain a numeric `hit_die`, typed `progression` rows,
addressable `features`, `subclasses`, and resolved `spell_ids`. A progression row
contains `level`, `proficiency_bonus`, ordered `feature_ids`, and ordered
class-specific resources as `{id, value}` records. This preserves variable class
tables without reducing them to markdown or an untyped property object.

Features and subclasses have deterministic IDs, source provenance, and content
segments. Class headings are discovered structurally from regions containing a
valid level-progression table; a hard-coded inventory of class names may only be
used as an acceptance baseline.

### Rules

Rules are flat, addressable records rather than nested anonymous children. Every
record has a path-aware ID, `title`, nullable `parent_id`, heading `depth`,
zero-based sibling `order`, provenance, and content segments. Parent IDs and
ordering allow exact reconstruction of the source tree while avoiding collisions
between repeated titles in different contexts or source sections.

Paragraph nodes following a heading belong to that rule until the next heading.
Lists and tables must either be represented in rule content structurally or be
reported with an explicit ignored-node reason; they cannot disappear silently.
