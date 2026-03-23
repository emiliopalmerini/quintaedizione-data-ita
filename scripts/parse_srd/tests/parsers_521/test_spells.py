# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for spell subtitle parsing — SRD 5.2.1."""

from __future__ import annotations

from ...parsers.spells import _parse_subtitle


class TestParseSubtitle521:
    """SRD 5.2.1 subtitle format: includes class list in parentheses."""

    def test_cantrip(self):
        level, school, classes = _parse_subtitle(
            "Trucchetto di Ammaliamento (Bardo, Stregone, Warlock)"
        )
        assert level == 0
        assert school == "Ammaliamento"
        assert classes == ["Bardo", "Stregone", "Warlock"]

    def test_leveled_with_ordinal_indicator(self):
        level, school, classes = _parse_subtitle(
            "Invocazione di 3º livello (Mago, Stregone)"
        )
        assert level == 3
        assert school == "Invocazione"
        assert classes == ["Mago", "Stregone"]
