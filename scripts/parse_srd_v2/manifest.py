"""Manifest and metadata helpers for parser v2."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .profiles import SourceProfile


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Metadata recorded for the source PDF."""

    id: str
    title: str
    path: str
    checksum_sha256: str
    page_count: int
    profile: str


@dataclass(frozen=True, slots=True)
class GeneratedMetadata:
    """Metadata recorded for one parser run."""

    parser: str
    parser_version: str
    generated_at: str


@dataclass(frozen=True, slots=True)
class Manifest:
    """Top-level run manifest."""

    source: SourceMetadata
    generated: GeneratedMetadata
    paths: dict[str, str]


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    """Return the SHA-256 checksum for a file."""

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_metadata(
    pdf_path: Path,
    *,
    profile: SourceProfile,
    page_count: int,
) -> SourceMetadata:
    """Build source metadata for a PDF."""

    return SourceMetadata(
        id=profile.source_id,
        title=profile.title,
        path=str(pdf_path),
        checksum_sha256=file_sha256(pdf_path),
        page_count=page_count,
        profile=profile.name,
    )


def generated_metadata() -> GeneratedMetadata:
    """Build parser generation metadata."""

    return GeneratedMetadata(
        parser="parse_srd_v2",
        parser_version=__version__,
        generated_at=utc_now_iso(),
    )


def to_jsonable(value: Any) -> Any:
    """Convert dataclasses and paths to JSON-compatible values."""

    if dataclasses.is_dataclass(value):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def write_json(path: Path, data: Any) -> None:
    """Write deterministic UTF-8 JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_jsonable(data), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    """Read UTF-8 JSON."""

    return json.loads(path.read_text(encoding="utf-8"))
