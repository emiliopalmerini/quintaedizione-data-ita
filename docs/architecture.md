# Architecture

Purpose: describe the target parser architecture and subsystem boundaries.
Audience: maintainers, parser implementers, and LLM agents.
Status: target design.
Canonical for: pipeline stages and responsibility boundaries.

## System Shape

```text
SRD 5.2.1 PDF
  -> extraction artifacts
  -> normalized document model
  -> section tree
  -> typed entity parsers
  -> reference resolution
  -> schema v2 JSON
  -> validation reports
  -> versioned JSON bundle
```

The parser is a compiler pipeline. Each stage consumes a stable artifact from
the previous stage and emits a stable artifact for the next stage.

## Subsystems

Extraction reads the PDF and records page text, spans, words, blocks, fonts,
coordinates, line direction, page sizes, and source metadata. It does not create
SRD entities or discard layout evidence needed by later stages.

Normalization converts raw extraction output into a discriminated document model
with reading order, paragraphs, headings, lists, tables, sidebars, stat-block
regions, and page anchors. Structured tables retain rows, columns, cells, and
source geometry; they are not flattened into prose or markdown.

Sectioning builds a heading tree and assigns each node to a known SRD section.
Heading identity defines boundaries; expected page ranges are validation guards.
It is responsible for detecting unassigned or unexpected required content.

Typed parsers convert section nodes into schema v2 entities. They may use
regular expressions inside known entity boundaries, but must not parse the whole
PDF with global regular expressions.

Reference resolution builds catalogs from parsed entities and controlled SRD
vocabularies, then converts eligible text spans into typed, qualified references.
Ambiguous candidates remain text and are reported instead of guessed.

Validation enforces schema rules, semantic rules, ID uniqueness, reference
integrity, and expected coverage.

Publication writes a bundle manifest and one canonical JSON file per collection.
The manifest records source identity, schema and dataset versions, file hashes,
record counts, parser version, locale, and report paths.

## Artifact Boundaries

Intermediate artifacts are part of the build contract, not debug leftovers. The
pipeline should be able to stop after extraction, normalization, sectioning, or
parsing and resume from the prior artifact.

Artifacts should be byte-for-byte deterministic for the same input PDF, parser
version, and configuration. Generated JSON uses stable ordering and excludes
wall-clock timestamps and caller-specific absolute paths.

## Failure Modes

The parser must fail the build when:

- The source PDF cannot be identified as the expected SRD 5.2.1 document.
- A required section is missing or unmapped.
- Required entity fields are empty.
- Entity IDs collide within the same source edition.
- A content reference points to a missing entity.
- A required parser stage emits low-confidence or unknown content without an
  explicit report entry.
- A normalized node is neither parsed nor explicitly ignored with a reason.
- A generated artifact differs between equivalent deterministic builds.

Warnings are acceptable only for non-required enrichment, such as optional
cross-reference opportunities or cosmetic markdown normalization.

## Data Modeling Rules

- Entity identity is `(source_id, collection, id)` even while v1 targets one
  source edition.
- Builder-relevant values are typed fields, records, or references, not only
  rendered content.
- Class progression, equipment choices, prerequisites, actions, spellcasting,
  and source tables remain structurally queryable.
- Rules are addressable records with parent IDs and sibling order while still
  allowing consumers to reconstruct the source hierarchy.
- Repeated concepts such as abilities, skills, sizes, conditions, damage types,
  creature types, and languages use controlled vocabulary IDs.
- Rich content preserves readable text and may contain qualified references;
  source formatting is not a substitute for domain structure.
