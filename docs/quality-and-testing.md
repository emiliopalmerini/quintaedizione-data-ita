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
- Collection-specific semantic validation.
- Normalized-node accounting.
- Deterministic bundle reproduction.

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

The accepted SRD 5.2.1 checksum and reviewed semantic counts are versioned in
`scripts/parse_srd_v2/tests/baselines/srd-5.2.1-it.json`. Release qualification
must provide the source explicitly and run the full-PDF marker:

```bash
SRD_521_IT_PDF="$PWD/source/srd-5.2.1-it.pdf" \
  uv run pytest -m full_pdf scripts/parse_srd_v2/tests/test_full_pdf.py
```

The full-PDF test performs two builds in fresh directories, validates reviewed
collection and semantic counts, and compares every generated JSON artifact by
SHA-256. A missing source path skips this expensive test in ordinary fixture CI
but is not acceptable for release qualification.

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
- Quality checks pass with zero errors.
- A second equivalent build produces identical canonical bytes.
- Every required normalized node is consumed, retained, or intentionally
  ignored with a reason.

## Duplicate-ID Policy

Duplicate IDs are errors unless a documented compatibility rule explicitly
handles them.

Nested rules must use path-aware IDs in v2.

## Manual Review

Manual review should focus on:

- New warnings.
- Entity count changes.
- Diff report anomalies.
- Low-confidence fields.
- Unassigned source sections.

Manual edits to generated JSON are not the source of truth. Fix parser logic,
profiles, schemas, or source fixtures instead.

## Test Delivery Order

Each implementation slice follows red/green TDD:

1. Add the smallest extraction or normalized-document fixture that demonstrates
   the source structure.
2. Add a failing unit test for the stage contract or typed output.
3. Implement the narrow behavior needed by the fixture.
4. Add malformed and boundary fixtures before broadening the parser.
5. Run the affected unit tests, then the complete parser suite.

Full-PDF acceptance tests are added once the source PDF is available in the
developer environment. The PDF itself is not committed; its accepted checksum
and expected collection counts are versioned as test configuration.

## Schema Gates

Validation rejects unknown fields, wrong scalar types, invalid ID syntax, empty
required strings, incomplete provenance, source-ID mismatches, duplicate IDs,
invalid controlled vocabulary IDs, malformed choices, and broken references.
Validating only the common envelope is insufficient.
