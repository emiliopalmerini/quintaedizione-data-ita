from __future__ import annotations

from scripts.parse_srd_v2.cli import build_parser, main


def test_parser_exposes_contracted_commands() -> None:
    parser = build_parser()

    cases = [
        ("build", ["build", "input.pdf", "--output-dir", "out"]),
        ("extract", ["extract", "input.pdf", "--output-dir", "out"]),
        ("normalize", ["normalize", "extracted", "--output-dir", "out"]),
        ("parse", ["parse", "normalized", "--output-dir", "out"]),
        ("validate", ["validate", "v2"]),
    ]

    for command, argv in cases:
        args = parser.parse_args(argv)
        assert args.command == command


def test_validate_command_returns_failure_for_empty_directory(tmp_path) -> None:
    v2_dir = tmp_path / "v2"
    v2_dir.mkdir()

    assert main(["validate", str(v2_dir)]) == 1
