# quintaedizione-data-ita

Python data compiler for producing a complete, validated, versioned JSON bundle
from the Italian D&D SRD 5.2.1 PDF.

The parser rebuild is documented in the repo wiki:

- [Wiki index](docs/README.md)
- [Target vision](docs/vision.md)
- [Schema v2](docs/schema-v2.md)
- [Release process](docs/releasing.md)
- [LLM context](docs/llm-context.md)

## Current Status

The Python compiler covers all required SRD 5.2.1 sections and produces the
stable schema-v2 dataset. Existing Go packages and embedded JSON are retained
only as migration references; they are not release gates or runtime dependencies.

## Parser Command

```bash
uv run python -m scripts.parse_srd_v2 build path/to/srd-5.2.1.pdf --output-dir output/srd-5.2.1
uv run pytest
make quality PDF=path/to/srd-5.2.1.pdf
make release PDF=path/to/srd-5.2.1.pdf
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
