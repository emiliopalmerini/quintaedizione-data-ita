# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for magic items parser — SRD 5.2.1."""

from __future__ import annotations

from ...parsers.magic_items import _parse_subtitle


class TestParseSubtitle:
    """Magic item subtitle parsing (5.2.1)."""

    def test_standard(self):
        t, r, att, det = _parse_subtitle("Oggetto meraviglioso, raro")
        assert t == "Oggetto meraviglioso"
        assert r == "raro"
        assert att is False

    def test_with_attunement(self):
        t, r, att, det = _parse_subtitle(
            "Oggetto meraviglioso, non comune (richiede sintonia)"
        )
        assert t == "Oggetto meraviglioso"
        assert r == "non comune"
        assert att is True
        assert det == ""

    def test_with_attunement_details(self):
        t, r, att, det = _parse_subtitle(
            "Arma (qualsiasi spada), rara (richiede sintonia da un paladino)"
        )
        assert t == "Arma (qualsiasi spada)"
        assert r == "rara"
        assert att is True
        assert det == "da un paladino"

    def test_empty_on_no_match(self):
        t, r, att, det = _parse_subtitle("Not a subtitle")
        assert t == ""
        assert r == ""
