"""Stage orchestration for parser v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .collections import collection_ids
from .errors import UnsupportedStage
from .extract import extract_pdf
from .manifest import (
    Manifest,
    SourceMetadata,
    generated_metadata,
    read_json,
    write_json,
)
from .normalize import normalize_extracted
from .parsers import get_parser
from .profiles import SRD_521_IT
from .schema import empty_envelope, validate_envelope
from .sections import assign_sections


STAGE_DIRS = ("extracted", "normalized", "sections", "v2", "reports", "compat")


def ensure_output_tree(output_dir: Path) -> dict[str, Path]:
    """Create and return the contracted output tree."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: output_dir / name for name in STAGE_DIRS}
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _manifest_paths(output_dir: Path) -> dict[str, str]:
    return {
        "manifest": str(output_dir / "manifest.json"),
        **{name: str(output_dir / name) for name in STAGE_DIRS},
    }


def write_manifest(output_dir: Path, source: SourceMetadata) -> Manifest:
    """Write the top-level manifest for a parser run."""

    manifest = Manifest(
        source=source,
        generated=generated_metadata(),
        paths=_manifest_paths(output_dir),
    )
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def run_extract(pdf_path: Path, output_dir: Path) -> Path:
    """Run extraction and write raw artifacts."""

    paths = ensure_output_tree(output_dir)
    source, extracted = extract_pdf(pdf_path, profile=SRD_521_IT)
    write_json(paths["extracted"] / "pages.json", extracted)
    write_manifest(output_dir, source)
    return paths["extracted"] / "pages.json"


def run_normalize(extracted_dir: Path, output_dir: Path) -> Path:
    """Run normalization from an extracted artifact directory."""

    paths = ensure_output_tree(output_dir)
    extracted = read_json(extracted_dir / "pages.json")
    normalized = normalize_extracted(extracted)
    write_json(paths["normalized"] / "document.json", normalized)
    return paths["normalized"] / "document.json"


def _source_from_artifact(source: dict[str, Any]) -> SourceMetadata:
    return SourceMetadata(
        id=str(source.get("id", "")),
        title=str(source.get("title", "")),
        path=str(source.get("path", "")),
        checksum_sha256=str(source.get("checksum_sha256", "")),
        page_count=int(source.get("page_count", 0)),
        profile=str(source.get("profile", "")),
    )


def run_parse(normalized_dir: Path, output_dir: Path) -> Path:
    """Run section assignment and implemented typed parsers."""

    paths = ensure_output_tree(output_dir)
    document = read_json(normalized_dir / "document.json")
    sections_artifact = assign_sections(document)
    write_json(paths["sections"] / "sections.json", sections_artifact)

    source = _source_from_artifact(sections_artifact.get("source", {}))
    generated = generated_metadata()
    report: dict[str, Any] = {
        "stage": "parse",
        "collections": [],
        "errors": [],
        "unsupported_sections": [],
    }

    by_collection: dict[str, list[dict[str, Any]]] = {}
    for section in sections_artifact.get("sections", []):
        parser_name = section.get("parser")
        parser = get_parser(str(parser_name))
        if parser is None:
            report["unsupported_sections"].append(
                {
                    "section_id": section.get("id"),
                    "parser": parser_name,
                    "collection": section.get("collection"),
                }
            )
            continue

        items = parser(section, source.id)
        collection_id = str(section.get("collection", ""))
        by_collection.setdefault(collection_id, []).extend(items)
        report["collections"].append(
            {
                "collection": collection_id,
                "section_id": section.get("id"),
                "item_count": len(items),
            }
        )
        if not items:
            report["errors"].append(f"{section.get('id')}: parser produced no items")

    for collection_id, items in by_collection.items():
        envelope = empty_envelope(collection_id, source=source, generated=generated)
        envelope["items"] = items
        validation_errors = validate_envelope(envelope)
        if validation_errors:
            report["errors"].extend(
                f"{collection_id}: {error}" for error in validation_errors
            )
        write_json(paths["v2"] / f"{collection_id}.json", envelope)

    report_path = paths["reports"] / "parse.json"
    write_json(report_path, report)
    return report_path


def run_compat(_v2_dir: Path, _output_dir: Path) -> None:
    """Placeholder for compatibility JSON generation."""

    raise UnsupportedStage(
        "compat stage is not implemented yet; implement after schema v2 entities exist"
    )


def run_validate(v2_dir: Path) -> dict[str, Any]:
    """Validate all v2 envelopes in a directory and write a report."""

    files = sorted(v2_dir.glob("*.json"))
    report: dict[str, Any] = {
        "stage": "validate",
        "files": [],
        "errors": [],
    }

    if not files:
        report["errors"].append(f"no v2 JSON files found in {v2_dir}")

    expected = set(collection_ids())
    seen: set[str] = set()
    for path in files:
        data = read_json(path)
        errors = validate_envelope(data)
        collection = data.get("collection") if isinstance(data, dict) else None
        if isinstance(collection, str):
            seen.add(collection)
        report["files"].append(
            {
                "path": str(path),
                "collection": collection,
                "errors": errors,
            }
        )
        report["errors"].extend(f"{path.name}: {err}" for err in errors)

    missing = sorted(expected - seen)
    for collection_id in missing:
        report["errors"].append(f"missing collection envelope: {collection_id}")

    return report


def run_build(pdf_path: Path, output_dir: Path) -> None:
    """Run the implemented prefix of the full build pipeline."""

    extracted = run_extract(pdf_path, output_dir)
    run_normalize(extracted.parent, output_dir)
    run_parse(output_dir / "normalized", output_dir)
    run_compat(output_dir / "v2", output_dir / "compat")
