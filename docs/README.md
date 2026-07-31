# quintaedizione-data-ita Wiki

Purpose: entry point for the target documentation wiki.
Audience: maintainers, parser implementers, data curators, and LLM agents.
Status: target design for the clean parser rebuild.
Canonical for: wiki navigation and reading order.

This wiki defines the target architecture for rebuilding the SRD PDF parsing
pipeline. It describes the system we intend to build, not a complete inventory
of the legacy parser currently in the repository.

## Reading Paths

For maintainers:

1. Read [Vision](vision.md) to understand goals, non-goals, and constraints.
2. Read [Architecture](architecture.md) for subsystem boundaries.
3. Read [Quality and Testing](quality-and-testing.md) for acceptance gates.
4. Read [Releasing](releasing.md) before publishing a dataset.

For parser implementers:

1. Read [Pipeline Contracts](pipeline-contracts.md).
2. Read [Schema v2](schema-v2.md).
3. Read [Quality and Testing](quality-and-testing.md).

For data curators:

1. Read [Vision](vision.md).
2. Read [Schema v2](schema-v2.md).
3. Read [Quality and Testing](quality-and-testing.md).

For LLM agents:

1. Read [LLM Context](llm-context.md).
2. Read [Architecture](architecture.md).
3. Read [Pipeline Contracts](pipeline-contracts.md).

## Canonical Pages

- [Vision](vision.md): target outcome, scope, and defaults.
- [Architecture](architecture.md): high-level design and subsystem ownership.
- [Pipeline Contracts](pipeline-contracts.md): parser inputs, artifacts, CLI, and
  output directory rules.
- [Schema v2](schema-v2.md): canonical versioned JSON contract.
- [Quality and Testing](quality-and-testing.md): validation, fixtures, and
  regression policy.
- [LLM Context](llm-context.md): concise implementation guidance for agents.
- [Releasing](releasing.md): qualification, versioning, and archive publication.
- [Glossary](glossary.md): shared vocabulary.

## Documentation Rules

- Keep this wiki in plain Markdown.
- Prefer stable headings and explicit contracts over prose-only guidance.
- Update this wiki before changing parser architecture or schema behavior.
- Do not duplicate canonical guidance into prompts or tool-specific files; link
  back to the owning page instead.
