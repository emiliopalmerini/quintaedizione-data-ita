# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Tests for spell metadata field extraction — SRD 5.1."""

from __future__ import annotations

from ...classify import SpanRole
from ...merge import ClassifiedSpan, Paragraph
from ...parsers_51.spells import _extract_field
from ..helpers import para


def _para(text: str, role: SpanRole = SpanRole.BODY_ITALIC) -> Paragraph:
    """Create a single-span paragraph (5.1 uses BODY_ITALIC for subtitle)."""
    return Paragraph(
        spans=[ClassifiedSpan(text=text, role=role)],
        role=role,
        page_num=1,
    )


class TestExtractFieldSeparateParagraphs:
    """Fields on their own paragraph line."""

    def test_casting_time(self):
        paras = [_para("Tempo di lancio: 1 azione")]
        result = _extract_field(paras, "Tempo di lancio")
        assert result == "1 azione"

    def test_duration(self):
        paras = [_para("Durata: Istantanea")]
        result = _extract_field(paras, "Durata")
        assert result == "Istantanea"


class TestExtractFieldMergedParagraph:
    """All metadata merged into one paragraph (common in 5.1)."""

    def test_casting_time_from_merged(self):
        paras = [
            _para(
                "Trucchetto di Ammaliamento "
                "Tempo di lancio: 1 azione "
                "Gittata: 9 metri "
                "Componenti: V, S "
                "Durata: 1 round"
            ),
        ]
        result = _extract_field(paras, "Tempo di lancio")
        assert result == "1 azione"

    def test_gittata_from_merged(self):
        paras = [
            _para(
                "Trucchetto di Ammaliamento "
                "Tempo di lancio: 1 azione "
                "Gittata: 9 metri "
                "Componenti: V, S "
                "Durata: 1 round"
            ),
        ]
        result = _extract_field(paras, "Gittata")
        assert result == "9 metri"

    def test_components_from_merged(self):
        paras = [
            _para(
                "Trucchetto di Ammaliamento "
                "Tempo di lancio: 1 azione "
                "Gittata: 9 metri "
                "Componenti: V, S "
                "Durata: 1 round"
            ),
        ]
        result = _extract_field(paras, "Componenti")
        assert result == "V, S"

    def test_duration_no_bleed(self):
        paras = [
            _para(
                "Trucchetto di Ammaliamento "
                "Tempo di lancio: 1 azione "
                "Gittata: 9 metri "
                "Componenti: V, S "
                "Durata: 1 round"
            ),
        ]
        result = _extract_field(paras, "Durata")
        assert result == "1 round"

    def test_duration_concentration(self):
        paras = [
            _para(
                "Ammaliamento di 1° livello "
                "Tempo di lancio: 1 azione "
                "Gittata: 9 metri "
                "Componenti: V, S, M (un pezzo di filo) "
                "Durata: Concentrazione, fino a 1 minuto"
            ),
        ]
        result = _extract_field(paras, "Durata")
        assert result == "Concentrazione, fino a 1 minuto"

    def test_duration_instantaneous(self):
        paras = [
            _para(
                "Invocazione di 3° livello "
                "Tempo di lancio: 1 azione "
                "Gittata: 45 metri "
                "Componenti: V, S, M (guano di pipistrello e zolfo) "
                "Durata: Istantanea "
                "Una scia di luce brillante parte dall'indice."
            ),
        ]
        result = _extract_field(paras, "Durata")
        assert result == "Istantanea"

    def test_duration_with_double_space(self):
        paras = [
            _para(
                "Abiurazione di 2° livello "
                "Tempo di lancio: 1 azione "
                "Gittata: 9 metri "
                "Componenti: V, S "
                "Durata: 8 ore  Questo incantesimo rafforza."
            ),
        ]
        result = _extract_field(paras, "Durata")
        assert result == "8 ore"

    def test_duration_period_before_description(self):
        paras = [
            _para(
                "Trasmutazione di 2° livello "
                "Tempo di lancio: 1 azione "
                "Gittata: Contatto "
                "Componenti: V, S, M "
                "Durata: Concentrazione, fino a 1 ora. "
                "L'incantatore tocca una creatura e le concede un potenziamento."
            ),
        ]
        result = _extract_field(paras, "Durata")
        assert result == "Concentrazione, fino a 1 ora"
