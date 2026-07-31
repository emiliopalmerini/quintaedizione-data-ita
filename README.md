# quintaedizione-data-ita

Python data compiler for producing a complete, validated, versioned JSON bundle
from the Italian D&D SRD 5.2.1 PDF.

The parser rebuild is documented in the repo wiki:

- [Wiki index](docs/README.md)
- [Target vision](docs/vision.md)
- [Schema v2](docs/schema-v2.md)
- [LLM context](docs/llm-context.md)

## Current Status

The `v2` branch is rebuilding the parser around loss-preserving intermediate
artifacts and strict typed output. Existing Go packages and embedded JSON remain
temporarily as migration references; they are not the target runtime.

## Parser Command

```bash
uv run python -m scripts.parse_srd_v2 build path/to/srd-5.2.1.pdf --output-dir output/srd-5.2.1
uv run pytest
```

The published data contract is a bundle containing `manifest.json`, typed JSON
collection files, intermediate artifacts, and machine-readable quality reports.

## Target Pipeline

```text
SRD PDF -> extraction -> normalized document -> sections -> typed entities
        -> reference resolution -> validation -> versioned JSON bundle
```

## License

- Code: [BSD 3-Clause](LICENSE)
- SRD content: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
  by Wizards of the Coast.
