# quintaedizione-data-ita

Go module that provides Italian D&D SRD data as typed structs backed by embedded
JSON.

The parser rebuild is documented in the repo wiki:

- [Wiki index](docs/README.md)
- [Target vision](docs/vision.md)
- [Schema v2](docs/schema-v2.md)
- [LLM context](docs/llm-context.md)

## Requirements

- Go 1.25.7

## Common Commands

```bash
make test
make quality
go test ./...
nix-shell -p python313 python313Packages.pymupdf python313Packages.pytest --run 'pytest scripts/parse_srd_v2/tests -q'
```

## Current Runtime Shape

```text
embedded JSON -> Go structs -> in-memory store -> typed accessors/search
```

Main packages:

- `srd`: typed SRD entities and content segments.
- `store`: embedded data loading, indexes, typed accessors, and search entry
  point.
- `search` and `filters`: helper packages for consumers.
- `encounter`, `maps`, and `generators`: additional embedded data domains.
- `scripts`: parser and data tooling.

## License

- Code: [BSD 3-Clause](LICENSE)
- SRD content: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
  by Wizards of the Coast.
