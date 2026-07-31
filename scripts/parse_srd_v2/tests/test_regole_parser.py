from __future__ import annotations

from scripts.parse_srd_v2.parsers.regole import parse_regole


def test_parse_rules_flattens_hierarchy_with_path_aware_ids() -> None:
    nodes = [
        ("heading", 1, "Come si gioca"),
        ("paragraph", None, "Le regole fondamentali."),
        ("heading", 2, "Prove"),
        ("heading", 3, "Bonus di competenza"),
        ("paragraph", None, "Il bonus si applica alla prova."),
        ("heading", 2, "Tiri salvezza"),
        ("heading", 3, "Bonus di competenza"),
        ("paragraph", None, "Il bonus si applica al tiro."),
    ]
    section_nodes = []
    for index, (node_type, level, text) in enumerate(nodes, start=1):
        node = {
            "id": f"p0005-n{index:04d}",
            "type": node_type,
            "text": text,
            "page_number": 5,
        }
        if level is not None:
            node["heading_level"] = level
        section_nodes.append(node)
    section = {
        "id": "come_si_gioca",
        "title": "Come si gioca",
        "page_start": 5,
        "page_end": 20,
        "nodes": section_nodes,
    }

    result = parse_regole(section, "srd-5.2.1-it")

    assert [item["id"] for item in result.items] == [
        "come-si-gioca",
        "come-si-gioca-prove",
        "come-si-gioca-prove-bonus-di-competenza",
        "come-si-gioca-tiri-salvezza",
        "come-si-gioca-tiri-salvezza-bonus-di-competenza",
    ]
    assert [item["parent_id"] for item in result.items] == [
        None,
        "come-si-gioca",
        "come-si-gioca-prove",
        "come-si-gioca",
        "come-si-gioca-tiri-salvezza",
    ]
    assert [item["order"] for item in result.items] == [0, 0, 0, 1, 0]
    assert [item["depth"] for item in result.items] == [1, 2, 3, 2, 3]
    assert result.items[0]["content"] == [
        {"type": "text", "text": "Le regole fondamentali."}
    ]
    assert result.items[2]["content"] == [
        {"type": "text", "text": "Il bonus si applica alla prova."}
    ]
    assert result.consumed_node_ids == [node["id"] for node in section_nodes]
    assert result.ignored_nodes == []
