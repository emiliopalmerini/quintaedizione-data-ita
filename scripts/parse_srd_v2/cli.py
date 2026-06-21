"""CLI for parser v2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import ParseSRDError
from .manifest import to_jsonable, write_json
from .stages import (
    run_build,
    run_compat,
    run_extract,
    run_normalize,
    run_parse,
    run_validate,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser."""

    parser = argparse.ArgumentParser(
        prog="python -m scripts.parse_srd_v2",
        description="Parse Italian SRD 5.2.1 PDF into schema v2 artifacts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Run the full parser pipeline")
    build.add_argument("pdf", type=Path)
    build.add_argument("--output-dir", type=Path, required=True)

    extract = sub.add_parser("extract", help="Extract raw PDF layout artifacts")
    extract.add_argument("pdf", type=Path)
    extract.add_argument("--output-dir", type=Path, required=True)

    normalize = sub.add_parser("normalize", help="Normalize extracted artifacts")
    normalize.add_argument("extracted_dir", type=Path)
    normalize.add_argument("--output-dir", type=Path, required=True)

    parse = sub.add_parser("parse", help="Parse normalized document artifacts")
    parse.add_argument("normalized_dir", type=Path)
    parse.add_argument("--output-dir", type=Path, required=True)

    validate = sub.add_parser("validate", help="Validate schema v2 envelopes")
    validate.add_argument("v2_dir", type=Path)
    validate.add_argument("--report", type=Path)

    compat = sub.add_parser("compat", help="Generate legacy compatibility JSON")
    compat.add_argument("v2_dir", type=Path)
    compat.add_argument("--output-dir", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the parser CLI."""

    args = build_parser().parse_args(argv)
    try:
        if args.command == "build":
            run_build(args.pdf, args.output_dir)
            return 0
        if args.command == "extract":
            path = run_extract(args.pdf, args.output_dir)
            print(path)
            return 0
        if args.command == "normalize":
            path = run_normalize(args.extracted_dir, args.output_dir)
            print(path)
            return 0
        if args.command == "parse":
            run_parse(args.normalized_dir, args.output_dir)
            return 0
        if args.command == "validate":
            report = run_validate(args.v2_dir)
            if args.report:
                write_json(args.report, report)
            else:
                print(json.dumps(to_jsonable(report), ensure_ascii=False, indent=2, sort_keys=True))
            return 1 if report["errors"] else 0
        if args.command == "compat":
            run_compat(args.v2_dir, args.output_dir)
            return 0
    except ParseSRDError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    raise AssertionError(f"unhandled command: {args.command}")
