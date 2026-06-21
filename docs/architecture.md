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
  -> schema v2 JSON
  -> validation reports
  -> compatibility JSON
  -> Go embed/store tests
```

The parser is a compiler pipeline. Each stage consumes a stable artifact from
the previous stage and emits a stable artifact for the next stage.

## Subsystems

Extraction reads the PDF and records page text, spans, words, blocks, fonts,
coordinates, page sizes, and source metadata. It does not create SRD entities.

Normalization converts raw extraction output into a document model with reading
order, paragraphs, headings, tables, sidebars, stat blocks, and page anchors.

Sectioning builds a heading tree and assigns each node to a known SRD section.
It is responsible for detecting unassigned or unexpected required content.

Typed parsers convert section nodes into schema v2 entities. They may use
regular expressions inside known entity boundaries, but must not parse the whole
PDF with global regular expressions.

Reference resolution builds catalogs from parsed entities and fixed SRD terms,
then converts eligible text spans into typed content references.

Validation enforces schema rules, semantic rules, ID uniqueness, reference
integrity, and expected coverage.

Compatibility generation converts schema v2 entities into the current JSON files
used by the Go module.

## Artifact Boundaries

Intermediate artifacts are part of the build contract, not debug leftovers. The
pipeline should be able to stop after extraction, normalization, sectioning, or
parsing and resume from the prior artifact.

Artifacts should be deterministic for the same input PDF, parser version, and
configuration. Generated JSON must use stable ordering.

## Failure Modes

The parser must fail the build when:

- The source PDF cannot be identified as the expected SRD 5.2.1 document.
- A required section is missing or unmapped.
- Required entity fields are empty.
- Entity IDs collide within the same source edition.
- A content reference points to a missing entity.
- A required parser stage emits low-confidence or unknown content without an
  explicit report entry.

Warnings are acceptable only for non-required enrichment, such as optional
cross-reference opportunities or cosmetic markdown normalization.
