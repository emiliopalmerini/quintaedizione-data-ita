"""Command entry point for ``python -m scripts.parse_srd_v2``."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
