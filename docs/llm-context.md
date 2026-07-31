# LLM Context

Purpose: provide concise repo guidance for LLM agents.
Audience: LLM agents and maintainers supervising them.
Status: target design.
Canonical for: agent orientation before parser or documentation edits.

## First Files To Read

1. [docs/README.md](README.md)
2. [docs/vision.md](vision.md)
3. [docs/architecture.md](architecture.md)
4. [docs/pipeline-contracts.md](pipeline-contracts.md)
5. [docs/schema-v2.md](schema-v2.md)
6. [docs/quality-and-testing.md](quality-and-testing.md)

## Current Objective

The target is a clean Python data compiler for the Italian SRD 5.2.1 PDF,
generating a complete canonical schema v2 bundle as a manifest plus typed JSON
collection files.

Do not treat existing parser code as the final architecture. Use it as context
only unless a task explicitly asks to preserve or modify legacy behavior.

## Implementation Boundaries

- Python owns PDF extraction, normalization, parsing, validation, and bundle
  publication.
- Canonical generated data is schema v2.
- Source PDF identity, section coverage, schema validity, ID uniqueness, and
  reference integrity are hard gates.
- Existing Go code and JSON are migration references until v2 reaches complete
  coverage; they are not target contracts.

## Commands

Parser checks:

```bash
uv run pytest
```

Target parser commands are defined in [Pipeline Contracts](pipeline-contracts.md).
The current implementation is an early scaffold: CLI shape and extraction are
reusable, while normalization, sectioning, schema validation, and the first typed
parsers require alignment with the structural contracts before more collections
are added.

## Editing Rules

- Update canonical docs before changing target parser architecture.
- Keep generated data out of manual source-of-truth edits unless the task is
  explicitly about data curation.
- Do not duplicate long guidance from this wiki into prompts or local notes.
- If a task conflicts with this wiki, ask whether to update the wiki or follow
  the existing contract.
