---
name: srd-data-quality
description: Use when validating, auditing, comparing, or preparing a generated SRD schema-v2 JSON bundle or investigating parser quality reports.
---

# SRD Data Quality

Audit generated data as a compiler product, tracing failures back to the earliest
responsible pipeline stage.

## Required Context

Read:

1. `docs/schema-v2.md`
2. `docs/quality-and-testing.md`
3. `docs/pipeline-contracts.md`

These pages own the acceptance gates. Do not duplicate or weaken them in local
scripts, prompts, or reports.

## Audit Order

1. Verify source identity, checksum, page count, parser version, schema version,
   dataset version, and locale.
2. Verify every manifest file path, SHA-256 checksum, and declared item count.
3. Run strict envelope and collection-specific schema validation.
4. Check stable ID syntax, duplicate qualified IDs, source-ID consistency, and
   complete provenance.
5. Check required section coverage and normalized-node accounting. Distinguish
   consumed, retained, intentionally ignored, and unassigned nodes.
6. Check controlled vocabulary values and reference integrity. Report ambiguous
   candidates separately from broken references.
7. Compare collection counts and field coverage with the accepted baseline.
   Investigate drops rather than updating expectations automatically.
8. Compare two equivalent builds byte-for-byte to verify determinism.
9. Review confidence and diff reports for anomalies not represented by hard
   validation failures.

## Failure Classification

Classify each finding by its earliest cause:

- extraction: source text, geometry, font, or block evidence is absent;
- normalization: reading order or structural node type is wrong;
- sectioning: content belongs to the wrong or no section;
- typed parsing: entity boundaries or fields are incomplete;
- reference resolution: target selection is broken or ambiguous;
- schema/publication: invalid data passed validation or manifest metadata is
  inconsistent.

Fix the earliest responsible stage. Do not patch generated JSON or hide failures
through count-baseline changes.

## Reporting

Lead with errors ordered by severity and include artifact paths, entity IDs,
source pages, and report keys. State commands run and residual risks, especially
when the full source PDF or prior accepted bundle is unavailable.
