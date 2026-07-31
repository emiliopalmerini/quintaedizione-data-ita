"""Typed parser output and normalized-node accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ParseResult:
    """Entities plus an explicit disposition for source nodes."""

    items: list[dict[str, Any]]
    consumed_node_ids: list[str]
    ignored_nodes: list[dict[str, str]]


def node_ids(nodes: list[dict[str, Any]]) -> list[str]:
    """Return present normalized node IDs in source order."""

    return [node_id for node in nodes if isinstance(node_id := node.get("id"), str)]


def ignored_node_entries(
    nodes: list[dict[str, Any]],
    reason: str,
) -> list[dict[str, str]]:
    """Build ignored-node diagnostics for nodes carrying stable IDs."""

    return [{"node_id": node_id, "reason": reason} for node_id in node_ids(nodes)]
