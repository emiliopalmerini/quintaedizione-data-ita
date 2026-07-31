# Pipeline Contracts

Purpose: define target parser inputs, outputs, commands, and artifact rules.
Audience: parser implementers and LLM agents.
Status: target design.
Canonical for: parser CLI and data-flow contracts.

## Source Input

The v1 parser accepts one source PDF: the Italian SRD 5.2.1 document.

The parser must record:

- SHA-256 checksum.
- Page count.
- Parser version.
- Profile name.
- Run timestamp.

The parser must refuse to continue if the source profile does not match the
expected page count and recognizable font/layout markers.

## Target CLI

The target CLI should expose one main command:

```bash
python -m scripts.parse_srd_v2 build path/to/srd-5.2.1.pdf --output-dir output/srd-5.2.1
```

It should also expose inspectable stage commands:

```bash
python -m scripts.parse_srd_v2 extract path/to/srd-5.2.1.pdf --output-dir output/srd-5.2.1
python -m scripts.parse_srd_v2 normalize output/srd-5.2.1/extracted --output-dir output/srd-5.2.1
python -m scripts.parse_srd_v2 parse output/srd-5.2.1/normalized --output-dir output/srd-5.2.1
python -m scripts.parse_srd_v2 validate output/srd-5.2.1/v2
```

The command names are the contract; module layout can change during
implementation if the commands remain stable.

## Output Directory Contract

Each parser run writes to an explicit output directory:

```text
output/srd-5.2.1/
  manifest.json
  extracted/
  normalized/
  sections/
  v2/
  reports/
```

`manifest.json` records input metadata, parser and schema versions, locale,
collection record counts, relative generated file paths, and SHA-256 checksums.
It must not contain absolute source or output paths.

`extracted/` stores raw page and layout artifacts.

`normalized/` stores the document model after reading order, paragraph, table,
and block normalization.

`sections/` stores heading trees and section assignments.

`v2/` stores canonical schema v2 JSON.

`reports/` stores validation, confidence, coverage, and diff reports.

## Section Contract

Each required SRD section must have:

- Stable section ID.
- Human title.
- Source page range.
- Heading path.
- Parser owner.
- Expected output collection.
- Coverage status.

Unassigned required content is a validation error.

## Parser Contract

Each typed parser consumes section nodes and returns schema v2 entities plus
parser diagnostics.

Parser diagnostics must include:

- Entity count.
- Skipped nodes.
- Low-confidence fields.
- Unknown headings.
- Source page coverage.

Parsers must not write final files directly. File writing belongs to the
orchestrator.

Every normalized node in a required section must end in one of these states:

- consumed by an entity parser;
- retained as section-level content;
- explicitly ignored with a machine-readable reason;
- reported as an error.

## Build Contract

`build` runs extraction, normalization, sectioning, typed parsing, reference
resolution, validation, report generation, and manifest finalization. It returns
non-zero and does not present the bundle as complete when any hard gate fails.

Collection files are written in registry order and entities in deterministic ID
order unless source order is a documented semantic field. Canonical files do
not contain wall-clock timestamps. If operational run timing is needed, it is
written to a non-canonical report excluded from artifact checksums.

The first complete release targets only the Italian SRD 5.2.1 PDF. Supporting a
new source requires a new source profile, section map, fixtures, and acceptance
baseline; it must not weaken the 5.2.1 contracts.
