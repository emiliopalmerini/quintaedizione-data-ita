"""Create deterministic release archives from validated bundles."""

from __future__ import annotations

import argparse
import gzip
import io
import tarfile
from pathlib import Path

from .manifest import file_sha256, read_json


def create_release_archive(bundle_dir: Path, dist_dir: Path) -> tuple[Path, Path]:
    manifest_path = bundle_dir / "manifest.json"
    manifest = read_json(manifest_path)
    version = str(manifest["dataset_version"])
    archive_name = f"quintaedizione-data-ita-{version}.tar.gz"
    archive_path = dist_dir / archive_name
    checksum_path = dist_dir / f"{archive_name}.sha256"
    root_name = f"quintaedizione-data-ita-{version}"
    files = sorted(path for path in bundle_dir.rglob("*") if path.is_file())
    if manifest_path not in files:
        raise ValueError("bundle manifest is missing")

    dist_dir.mkdir(parents=True, exist_ok=True)
    with archive_path.open("wb") as raw_file:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_file, mtime=0) as gz_file:
            with tarfile.open(fileobj=gz_file, mode="w") as archive:
                for path in files:
                    relative = path.relative_to(bundle_dir)
                    data = path.read_bytes()
                    info = tarfile.TarInfo(f"{root_name}/{relative.as_posix()}")
                    info.size = len(data)
                    info.mode = 0o644
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, io.BytesIO(data))

    checksum_path.write_text(
        f"{file_sha256(archive_path)}  {archive_name}\n",
        encoding="ascii",
    )
    return archive_path, checksum_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    create_release_archive(args.bundle_dir, args.dist_dir)


if __name__ == "__main__":
    main()
