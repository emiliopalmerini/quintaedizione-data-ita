# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for spell subtitle parsing — SRD 5.1."""

from __future__ import annotations

from ...parsers_51.spells import _parse_subtitle, _OVERRIDES


class TestParseSubtitle51:
    """SRD 5.1 subtitle format: no class list, uses ° (degree sign)."""

    def test_cantrip_no_classes(self):
        level, school = _parse_subtitle("Trucchetto di Trasmutazione")
        assert level == 0
        assert school == "Trasmutazione"

    def test_leveled_degree_sign(self):
        level, school = _parse_subtitle("Illusione di 4° livello")
        assert level == 4
        assert school == "Illusione"

    def test_leveled_1st(self):
        level, school = _parse_subtitle("Ammaliamento di 1° livello")
        assert level == 1
        assert school == "Ammaliamento"

    def test_leveled_with_ritual(self):
        level, school = _parse_subtitle(
            "Abiurazione di 1° livello (rituale)"
        )
        assert level == 1
        assert school == "Abiurazione"

    def test_leveled_9th(self):
        level, school = _parse_subtitle("Evocazione di 9° livello")
        assert level == 9
        assert school == "Evocazione"

    def test_subtitle_with_trailing_metadata(self):
        level, school = _parse_subtitle(
            "Ammaliamento di 1° livello Tempo di lancio: 1 azione Gittata: 9 metri"
        )
        assert level == 1
        assert school == "Ammaliamento"

    def test_cantrip_with_trailing_metadata(self):
        level, school = _parse_subtitle(
            "Trucchetto di Invocazione Tempo di lancio: 1 azione"
        )
        assert level == 0
        assert school == "Invocazione"

    def test_unknown_returns_negative(self):
        level, school = _parse_subtitle("Not a spell subtitle")
        assert level == -1
        assert school == ""


class TestSpellOverrides:
    def test_creazione_duration(self):
        assert _OVERRIDES["creazione"]["duration"] == "Speciale"

    def test_dominare_persone_school(self):
        assert _OVERRIDES["dominare persone"]["school"] == "Ammaliamento"
