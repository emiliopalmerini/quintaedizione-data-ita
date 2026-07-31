# Vision

Purpose: define the target parser rebuild and its boundaries.
Audience: maintainers, parser implementers, and data curators.
Status: target design.
Canonical for: goals, non-goals, scope, and defaults.

## Goal

Build a clean, reproducible Python data compiler that converts the Italian SRD
5.2.1 PDF into a complete, validated, versioned JSON bundle suitable for
character builders, rules browsers, search indexes, and other consumers.

The pipeline should be understandable by humans and LLM agents without reading
the full implementation first.

## Defaults

- Source scope: Italian SRD 5.2.1 PDF for v1.
- Parser stack: Python for PDF extraction and parsing.
- Canonical data contract: schema v2 JSON.
- Distribution contract: a manifest plus typed collection JSON files.
- Existing Go code and compatibility JSON are migration references only. Remove
  them after the v2 bundle reaches full source coverage and data parity.
- Documentation format: repo-native Markdown under `docs/`.

## Non-Goals

- Do not optimize for parsing arbitrary PDFs.
- Do not rely on OCR for digitally-born PDFs.
- Do not make parser output depend on unchecked manual edits.
- Do not silently accept partial entities, duplicate IDs, broken references, or
  unparsed required sections.
- Do not preserve the current Go API or its storage constraints in schema v2.
- Do not add a runtime database or query service to this repository.

## Success Criteria

The rebuild is successful when:

- The parser can regenerate canonical v2 JSON from the SRD 5.2.1 PDF.
- Every generated entity has deterministic identity, provenance, and schema
  version information.
- Quality checks fail on duplicate IDs, missing required fields, broken
  references, malformed content segments, and unparsed required sections.
- Builder-relevant tables, choices, prerequisites, features, and stat blocks are
  represented structurally rather than embedded only in prose or markdown.
- A maintainer can inspect parser reports and understand what changed between
  two generated datasets.

## Design Principles

- Treat the PDF as source material, not as structured data.
- Preserve intermediate artifacts so extraction bugs are reproducible.
- Parse from document structure before using field-level regular expressions.
- Keep schemas stricter than the source PDF.
- Prefer explicit failure over low-confidence output.
- Make review focus on anomalies and diffs rather than full manual rereading.

## Delivery Plan

Implementation proceeds in dependency order. Later phases must not compensate
for missing structure in earlier phases with global regular expressions or
hard-coded entity inventories.

1. **Contracts and tooling**
   - Align this wiki and the CLI with a Python-only JSON compiler.
   - Add a root Python project, locked dependencies, tests, and CI commands.
   - Define deterministic artifact and manifest serialization.
2. **Document model**
   - Preserve words, spans, fonts, coordinates, line direction, blocks, and page
     anchors during extraction.
   - Normalize reading order and produce typed headings, paragraphs, lists,
     tables, sidebars, and stat-block regions without losing source geometry.
   - Build a heading tree and account for every normalized node.
3. **Schema and validation**
   - Publish strict machine-readable schemas for the bundle and every
     collection.
   - Reject unknown fields, invalid IDs, incomplete provenance, duplicate keys,
     broken references, and empty required values.
   - Add controlled vocabularies for repeated rules concepts.
4. **Typed parsers**
   - Rebuild origins, species, and feats on the structural document model.
   - Add equipment and spells, then classes and progression, magic items,
     monsters and animals, rules, and the glossary.
   - Add parser diagnostics and fixtures before each parser implementation.
5. **References and quality gates**
   - Resolve source- and collection-qualified references conservatively.
   - Fail on required unassigned content and unexpected count regressions.
   - Produce coverage, confidence, reference, summary, and optional diff reports.
6. **Publication and migration cleanup**
   - Build the complete SRD 5.2.1 bundle and compare it with legacy data for
     omissions.
   - Verify deterministic output from the pinned source PDF.
   - Remove the Go runtime, embedded compatibility data, and legacy parser only
     after the JSON bundle satisfies all acceptance gates.
