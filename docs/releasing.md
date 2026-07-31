# Releasing

Purpose: define stable dataset release qualification and publication.
Audience: maintainers publishing canonical JSON bundles.
Status: release contract.
Canonical for: versions, qualification commands, and archive contents.

## Versions

- `PARSER_VERSION` identifies compiler behavior.
- `DATASET_VERSION` identifies the published bundle.
- `SCHEMA_VERSION` identifies the JSON contract.
- Stable Git tags use `v<dataset-version>`.

Parser and dataset versions are defined in
`scripts/parse_srd_v2/version.py`. A schema-breaking change requires a schema
major-version change; parser-only fixes do not require a dataset release until
new canonical output is published.

## Qualification

A release requires the locked fixture suite and the pinned full-PDF gate:

```bash
uv sync --frozen --dev
uv run pytest

SRD_521_IT_PDF="$PWD/source/srd-5.2.1-it.pdf" \
  uv run pytest -m full_pdf scripts/parse_srd_v2/tests/test_full_pdf.py
```

The full-PDF gate verifies source identity, reviewed semantic baselines, schema
and reference integrity, complete node accounting, and byte-for-byte equivalent
JSON from two fresh builds.

## Build And Package

```bash
make release PDF=source/srd-5.2.1-it.pdf
```

The command builds `output/srd-5.2.1` and writes a deterministic archive plus a
SHA-256 checksum under `dist/`. The archive contains the manifest, canonical v2
collections, intermediate artifacts, and reports. It never contains the source
PDF. Archive members have normalized ordering, ownership, permissions, and
timestamps.

## Publication

Before creating a GitHub release:

1. Confirm the worktree is clean and the release commit is on the target branch.
2. Confirm parser, dataset, project metadata, and intended tag versions agree.
3. Run both qualification commands above in the supported Linux environment.
4. Build the archive twice and confirm identical checksums.
5. Publish the `.tar.gz` and `.sha256` files; do not publish the PDF.

Legacy Go tests and compatibility JSON are migration references and are not
release gates for schema v2. Canonical v2 duplicate and reference checks remain
mandatory.
