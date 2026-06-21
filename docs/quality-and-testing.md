# Quality and Testing

Purpose: define validation gates and regression strategy for the target parser.
Audience: maintainers, parser implementers, and data curators.
Status: target design.
Canonical for: parser acceptance criteria and test coverage expectations.

## Quality Gates

The parser output is unacceptable if any required gate fails:

- Source PDF identity check.
- Required section coverage.
- Schema validation.
- Required field validation.
- Duplicate ID validation.
- Reference integrity validation.
- Content segment validation.
- Compatibility JSON generation.
- Go store load and test validation.

Warnings may be emitted for optional enrichment and review hints, but warnings
must be counted and reported.

## Reports

Each build writes reports under `reports/`:

- `summary.json`: counts, warnings, errors, and stage status.
- `coverage.json`: source pages, sections, parsed nodes, and unassigned content.
- `confidence.json`: low-confidence fields and parser diagnostics.
- `references.json`: resolved references, unresolved references, and skipped
  reference candidates.
- `diff.json`: generated data differences against a chosen prior output when a
  baseline is provided.

Reports should be concise enough for humans to review and structured enough for
LLM agents to inspect.

## Fixture Strategy

Tests should use small stable fixtures rather than the full PDF whenever
possible.

Required fixture categories:

- Heading and section extraction.
- Spell entity with all field types.
- Monster stat block with actions, reactions, and abilities.
- Rule tree with repeated child titles.
- Equipment table rows.
- Magic item description with rarity and attunement.
- Content reference resolution.

Full-PDF tests should be reserved for integration validation.

## Regression Tests

Unit tests validate stage behavior in isolation:

- Font/layout classification.
- Reading order.
- Paragraph merging.
- Table recognition.
- Heading tree construction.
- Entity parsers.
- ID generation.
- Reference segment generation.

Integration tests validate:

- Build command completes for the SRD 5.2.1 PDF.
- Canonical v2 JSON passes validation.
- Compatibility JSON loads through the Go store.
- `go test ./...` passes.
- Quality checks pass with zero errors.

## Duplicate-ID Policy

Duplicate IDs are errors unless a documented compatibility rule explicitly
handles them.

Nested rules must use path-aware IDs in v2. Legacy compatibility output must
avoid silently overwriting one rule with another in the Go store.

## Manual Review

Manual review should focus on:

- New warnings.
- Entity count changes.
- Diff report anomalies.
- Low-confidence fields.
- Unassigned source sections.

Manual edits to generated JSON are not the source of truth. Fix parser logic,
profiles, schemas, or source fixtures instead.
