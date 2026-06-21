# Glossary

Purpose: define shared terms used in the parser rebuild documentation.
Audience: maintainers, parser implementers, data curators, and LLM agents.
Status: target design.
Canonical for: documentation vocabulary.

## Terms

Canonical JSON: the schema v2 output that represents the parser's source of
truth.

Compatibility JSON: generated JSON shaped for the current Go structs and store.

Content segment: one ordered piece of rich text, either plain text or a typed
reference to another entity.

Data compiler: a deterministic pipeline that turns source material into
validated structured data.

Entity: one SRD item such as a spell, monster, rule, origin, or glossary
entry.

Extraction artifact: raw output from reading the PDF, including text, spans,
fonts, coordinates, pages, and blocks.

Heading tree: hierarchical representation of headings and their child content.

Low-confidence field: parsed data that passed a parser heuristic but should be
reviewed because the source shape was ambiguous or unexpected.

Normalized document model: layout-aware intermediate representation after raw
extraction and before typed parsing.

Parser profile: configuration that identifies and classifies a specific PDF's
fonts, colors, page ranges, and layout conventions.

Provenance: metadata linking generated data back to source pages, sections, and
parser stages.

Required section: SRD source section that must be assigned to a parser and
covered by output.

Schema v2: the target versioned JSON contract documented in
[Schema v2](schema-v2.md).

Source edition: a specific SRD source identity, such as `srd-5.2.1-it`.
