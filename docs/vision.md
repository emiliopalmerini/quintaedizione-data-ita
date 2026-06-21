# Vision

Purpose: define the target parser rebuild and its boundaries.
Audience: maintainers, parser implementers, and data curators.
Status: target design.
Canonical for: goals, non-goals, scope, and defaults.

## Goal

Build a clean, reproducible data compiler that converts the Italian SRD 5.2.1
PDF into validated, versioned JSON data and compatibility JSON for the current
Go module.

The pipeline should be understandable by humans and LLM agents without reading
the full implementation first.

## Defaults

- Source scope: Italian SRD 5.2.1 PDF for v1.
- Parser stack: Python for PDF extraction and parsing.
- Runtime library: Go module with embedded JSON remains separate from parser
  tooling.
- Canonical data contract: schema v2 JSON.
- Compatibility contract: generate current v1-style JSON until the Go API is
  intentionally migrated.
- Documentation format: repo-native Markdown under `docs/`.

## Non-Goals

- Do not optimize for parsing arbitrary PDFs.
- Do not rely on OCR for digitally-born PDFs.
- Do not make parser output depend on unchecked manual edits.
- Do not silently accept partial entities, duplicate IDs, broken references, or
  unparsed required sections.
- Do not change the public Go API as part of the documentation-first phase.

## Success Criteria

The rebuild is successful when:

- The parser can regenerate canonical v2 JSON from the SRD 5.2.1 PDF.
- Every generated entity has deterministic identity, provenance, and schema
  version information.
- Compatibility JSON can be generated for the existing Go store.
- Quality checks fail on duplicate IDs, missing required fields, broken
  references, malformed content segments, and unparsed required sections.
- A maintainer can inspect parser reports and understand what changed between
  two generated datasets.

## Design Principles

- Treat the PDF as source material, not as structured data.
- Preserve intermediate artifacts so extraction bugs are reproducible.
- Parse from document structure before using field-level regular expressions.
- Keep schemas stricter than the source PDF.
- Prefer explicit failure over low-confidence output.
- Make review focus on anomalies and diffs rather than full manual rereading.
