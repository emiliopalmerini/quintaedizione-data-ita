# Repository Instructions

This repository contains a Go data module and parser tooling for the Italian
D&D SRD data.

Before editing parser architecture, generated data contracts, or documentation,
read:

1. [docs/README.md](docs/README.md)
2. [docs/llm-context.md](docs/llm-context.md)

The `docs/` wiki is the source of truth for the target parser rebuild. Do not
duplicate its guidance into prompts, scripts, or local notes; link to the owning
page instead.

## Working Rules

- Keep parser rebuild work aligned with the target docs before changing code.
- Treat generated compatibility JSON as output, not hand-authored source of
  truth, unless a task explicitly asks for data curation.
- Run `go test ./...` for general validation.
- Run `go test -tags=quality ./store/` when changing generated SRD data,
  parser output, or validation rules.
