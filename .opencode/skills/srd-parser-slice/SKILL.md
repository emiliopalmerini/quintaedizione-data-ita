---
name: srd-parser-slice
description: Use when adding or changing SRD PDF extraction, normalization, sectioning, typed collection parsers, or parser fixtures under scripts/parse_srd_v2.
---

# SRD Parser Slice

Implement one vertical parser behavior at a time using red/green TDD.

## Required Context

Read these contracts before proposing or editing parser behavior:

1. `docs/llm-context.md`
2. `docs/architecture.md`
3. `docs/pipeline-contracts.md`
4. `docs/schema-v2.md`
5. `docs/quality-and-testing.md`

The wiki is authoritative. Update its owning page before implementing a change
that alters architecture, artifact contracts, schema behavior, or quality gates.

## Workflow

1. Identify the earliest pipeline stage where the required source information
   is missing or corrupted. Fix that stage instead of compensating downstream.
2. Add the smallest source-shaped fixture that demonstrates the behavior,
   including page anchors and relevant layout metadata.
3. Write and run a failing test. Confirm it fails for the intended reason.
4. Implement the smallest correct change in one file at a time.
5. Verify that transformed nodes retain provenance and that no source node is
   silently dropped.
6. For typed entities, validate required fields, stable IDs, deterministic
   ordering, and source-qualified references.
7. Run the narrow affected test, then the complete v2 parser suite.
8. Report tests run, remaining unsupported structure, and any full-PDF coverage
   that could not be verified.

## Guardrails

- Preserve source geometry until the stage that no longer needs it.
- Keep tables, choices, prerequisites, progression, and stat blocks structured.
- Do not discover entities from a hard-coded complete name list. Expected names
  may be used as an acceptance check after structural discovery.
- Do not use broad regular expressions across the whole document.
- Do not weaken validation to accommodate incomplete parser output.
- Do not hand-edit generated JSON as the source of truth.
- Do not add Go compatibility constraints to schema v2.
