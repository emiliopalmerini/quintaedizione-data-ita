"""Shared test helpers for parser tests."""

from __future__ import annotations

from ..classify import SpanRole
from ..heading_tree import HeadingNode as _RealHeadingNode
from ..merge import ClassifiedSpan, Paragraph

_LEVEL_TO_ROLE = {
    1: SpanRole.H1, 2: SpanRole.H2, 3: SpanRole.H3,
    4: SpanRole.H4, 5: SpanRole.H5, 6: SpanRole.H6,
}


def HeadingNode(title: str, level: int, content: list, children: list) -> _RealHeadingNode:
    return _RealHeadingNode(
        level=level, title=title, role=_LEVEL_TO_ROLE[level],
        content=content, children=children,
    )


def span(text: str, role: SpanRole) -> ClassifiedSpan:
    return ClassifiedSpan(text=text, role=role)


def para(text: str, role: SpanRole = SpanRole.BODY) -> Paragraph:
    return Paragraph(
        spans=[ClassifiedSpan(text=text, role=role)],
        role=role,
        page_num=1,
    )


def multi_para(spans: list[ClassifiedSpan], role: SpanRole | None = None) -> Paragraph:
    return Paragraph(
        spans=spans,
        role=role or spans[0].role,
        page_num=1,
    )
