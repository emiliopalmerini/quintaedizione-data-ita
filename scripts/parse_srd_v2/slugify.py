"""Slug helpers for parser v2."""

from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Return a deterministic lowercase ASCII slug."""

    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    return ascii_text.strip("-")
