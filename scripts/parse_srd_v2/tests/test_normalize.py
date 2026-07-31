from __future__ import annotations

from scripts.parse_srd_v2.normalize import normalize_extracted


def _span(text: str) -> dict:
    return {
        "text": text,
        "font": "Cambria",
        "size": 10.0,
        "color": 0,
        "flags": 0,
        "bbox": [0.0, 0.0, 0.0, 0.0],
    }


def test_normalize_builds_ordered_structural_nodes() -> None:
    extracted = {
        "source": {"id": "fixture"},
        "pages": [
            {
                "page_number": 1,
                "width": 600.0,
                "height": 800.0,
                "words": [
                    {
                        "text": "Destra",
                        "bbox": [340.0, 50.0, 390.0, 62.0],
                        "block_index": 0,
                        "line_index": 0,
                        "word_index": 0,
                    },
                    {
                        "text": "combi\u00ad",
                        "bbox": [20.0, 50.0, 60.0, 62.0],
                        "block_index": 1,
                        "line_index": 0,
                        "word_index": 0,
                    },
                    {
                        "text": "nazione",
                        "bbox": [20.0, 64.0, 65.0, 76.0],
                        "block_index": 1,
                        "line_index": 1,
                        "word_index": 0,
                    },
                ],
                "blocks": [
                    {
                        "bbox": [330.0, 50.0, 500.0, 62.0],
                        "lines": [
                            {
                                "bbox": [340.0, 50.0, 390.0, 62.0],
                                "writing_mode": 0,
                                "direction": [1.0, 0.0],
                                "spans": [_span("Destra")],
                            }
                        ],
                    },
                    {
                        "bbox": [20.0, 50.0, 200.0, 76.0],
                        "lines": [
                            {
                                "bbox": [20.0, 50.0, 60.0, 62.0],
                                "writing_mode": 0,
                                "direction": [1.0, 0.0],
                                "spans": [_span("combi\u00ad")],
                            },
                            {
                                "bbox": [20.0, 64.0, 65.0, 76.0],
                                "writing_mode": 0,
                                "direction": [1.0, 0.0],
                                "spans": [_span("nazione")],
                            },
                        ],
                    },
                ],
            }
        ],
    }

    document = normalize_extracted(extracted)

    nodes = document["pages"][0]["nodes"]
    assert [node["id"] for node in nodes] == ["p0001-n0001", "p0001-n0002"]
    assert [node["text"] for node in nodes] == ["combinazione", "Destra"]
    assert nodes[0]["type"] == "paragraph"
    assert nodes[0]["bbox"] == [20.0, 50.0, 65.0, 76.0]
    assert nodes[0]["source_block_index"] == 1
    assert nodes[0]["source_line_indexes"] == [0, 1]
    assert [word["text"] for word in nodes[0]["words"]] == ["combi\u00ad", "nazione"]
    assert [span["text"] for span in nodes[0]["spans"]] == ["combi\u00ad", "nazione"]


def test_normalize_orders_spanning_heading_before_columns() -> None:
    heading_span = _span("Capitolo")
    heading_span.update({"font": "GillSans-Bold", "size": 23.0, "color": 0x8C2220})
    extracted = {
        "source": {"id": "fixture"},
        "pages": [
            {
                "page_number": 1,
                "width": 600.0,
                "height": 800.0,
                "words": [],
                "blocks": [
                    {
                        "bbox": [20.0, 20.0, 580.0, 45.0],
                        "lines": [
                            {
                                "bbox": [20.0, 20.0, 580.0, 45.0],
                                "spans": [heading_span],
                            }
                        ],
                    },
                    {
                        "bbox": [330.0, 60.0, 500.0, 72.0],
                        "lines": [
                            {"bbox": [330.0, 60.0, 500.0, 72.0], "spans": [_span("Destra")]}
                        ],
                    },
                    {
                        "bbox": [20.0, 60.0, 200.0, 72.0],
                        "lines": [
                            {"bbox": [20.0, 60.0, 200.0, 72.0], "spans": [_span("Sinistra")]}
                        ],
                    },
                ],
            }
        ],
    }

    document = normalize_extracted(extracted)

    nodes = document["pages"][0]["nodes"]
    assert [node["text"] for node in nodes] == ["Capitolo", "Sinistra", "Destra"]
    assert nodes[0]["type"] == "heading"
    assert nodes[0]["heading_level"] == 1


def test_normalize_tracks_heading_paths_across_pages() -> None:
    chapter_span = _span("Capitolo")
    chapter_span.update({"font": "GillSans-Bold", "size": 23.0, "color": 0x8C2220})
    topic_span = _span("Argomento")
    topic_span.update({"font": "GillSans-Bold", "size": 16.0, "color": 0x8C2220})
    extracted = {
        "source": {"id": "fixture"},
        "pages": [
            {
                "page_number": 1,
                "width": 600.0,
                "height": 800.0,
                "words": [],
                "blocks": [
                    {
                        "bbox": [20.0, 20.0, 580.0, 45.0],
                        "lines": [{"bbox": [20.0, 20.0, 580.0, 45.0], "spans": [chapter_span]}],
                    },
                    {
                        "bbox": [20.0, 60.0, 200.0, 72.0],
                        "lines": [{"bbox": [20.0, 60.0, 200.0, 72.0], "spans": [_span("Introduzione")]}],
                    },
                ],
            },
            {
                "page_number": 2,
                "width": 600.0,
                "height": 800.0,
                "words": [],
                "blocks": [
                    {
                        "bbox": [20.0, 20.0, 200.0, 40.0],
                        "lines": [{"bbox": [20.0, 20.0, 200.0, 40.0], "spans": [topic_span]}],
                    },
                    {
                        "bbox": [20.0, 50.0, 200.0, 62.0],
                        "lines": [{"bbox": [20.0, 50.0, 200.0, 62.0], "spans": [_span("Dettagli")]}],
                    },
                ],
            },
        ],
    }

    document = normalize_extracted(extracted)

    page_one_nodes = document["pages"][0]["nodes"]
    page_two_nodes = document["pages"][1]["nodes"]
    assert page_one_nodes[0]["heading_path"] == ["Capitolo"]
    assert page_one_nodes[1]["heading_path"] == ["Capitolo"]
    assert page_two_nodes[0]["heading_path"] == ["Capitolo", "Argomento"]
    assert page_two_nodes[1]["heading_path"] == ["Capitolo", "Argomento"]
