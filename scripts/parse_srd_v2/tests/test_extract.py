from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts.parse_srd_v2 import extract
from scripts.parse_srd_v2.profiles import SourceProfile


class _FakePage:
    rect = SimpleNamespace(width=595.0, height=842.0)

    def get_text(self, kind: str):
        if kind == "text":
            return "Titolo\n"
        if kind == "words":
            return [(10.0, 20.0, 42.0, 32.0, "Titolo", 0, 0, 0)]
        if kind == "dict":
            return {
                "blocks": [
                    {
                        "type": 0,
                        "bbox": (10.0, 20.0, 42.0, 32.0),
                        "lines": [
                            {
                                "bbox": (10.0, 20.0, 42.0, 32.0),
                                "wmode": 0,
                                "dir": (1.0, 0.0),
                                "spans": [
                                    {
                                        "text": "Titolo",
                                        "font": "GillSans-Bold",
                                        "size": 16.0,
                                        "color": 0x8C2220,
                                        "flags": 20,
                                        "ascender": 1.0,
                                        "descender": -0.25,
                                        "origin": (10.0, 30.0),
                                        "bbox": (10.0, 20.0, 42.0, 32.0),
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        raise AssertionError(f"unexpected text kind: {kind}")


class _FakeDocument:
    def __iter__(self):
        return iter([_FakePage()])

    def __len__(self) -> int:
        return 1


def test_extract_preserves_words_and_line_metadata(monkeypatch, tmp_path: Path) -> None:
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"fake pdf")
    profile = SourceProfile(
        name="fixture",
        source_id="fixture",
        title="Fixture",
        expected_page_count=1,
        required_font_markers=("GillSans",),
    )
    monkeypatch.setattr(
        extract,
        "_fitz_module",
        lambda: SimpleNamespace(open=lambda _path: _FakeDocument()),
    )

    _, artifact = extract.extract_pdf(pdf, profile=profile)

    page = artifact["pages"][0]
    assert page["words"] == [
        {
            "text": "Titolo",
            "bbox": [10.0, 20.0, 42.0, 32.0],
            "block_index": 0,
            "line_index": 0,
            "word_index": 0,
        }
    ]
    line = page["blocks"][0]["lines"][0]
    assert line["writing_mode"] == 0
    assert line["direction"] == [1.0, 0.0]
    assert line["spans"][0]["flags"] == 20
    assert line["spans"][0]["ascender"] == 1.0
    assert line["spans"][0]["descender"] == -0.25
    assert line["spans"][0]["origin"] == [10.0, 30.0]
