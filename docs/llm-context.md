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

The target is a clean Python parser pipeline for the Italian SRD 5.2.1 PDF,
generating canonical schema v2 JSON and compatibility JSON for the current Go
module.

Do not treat existing parser code as the final architecture. Use it as context
only unless a task explicitly asks to preserve or modify legacy behavior.

## Implementation Boundaries

- Python owns PDF extraction and parsing.
- Go owns the embedded runtime data library.
- Canonical generated data is schema v2.
- Current Go-compatible JSON is generated compatibility output.
- Source PDF identity, section coverage, schema validity, ID uniqueness, and
  reference integrity are hard gates.

## Commands

Existing repo checks:

```bash
go test ./...
go test -tags=quality ./store/
nix-shell -p python313 python313Packages.pymupdf python313Packages.pytest --run 'pytest scripts/parse_srd_v2/tests -q'
```

Target parser commands are defined in
[Pipeline Contracts](pipeline-contracts.md). In the initial implementation
slice, extraction, normalization, CLI shape, and schema validation exist; typed
entity parsing and compatibility generation may still return explicit
unsupported-stage errors until their slices are implemented.

## Editing Rules

- Update canonical docs before changing target parser architecture.
- Keep generated data out of manual source-of-truth edits unless the task is
  explicitly about data curation.
- Do not duplicate long guidance from this wiki into prompts or local notes.
- If a task conflicts with this wiki, ask whether to update the wiki or follow
  the existing contract.
