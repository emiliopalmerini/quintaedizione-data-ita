"""Source profiles for parser v2."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import SourceIdentityError


@dataclass(frozen=True, slots=True)
class SourceProfile:
    """Expected identity and layout markers for a source PDF."""

    name: str
    source_id: str
    title: str
    expected_page_count: int
    required_font_markers: tuple[str, ...]


SRD_521_IT = SourceProfile(
    name="srd-5.2.1-it",
    source_id="srd-5.2.1-it",
    title="System Reference Document 5.2.1 Italiano",
    expected_page_count=405,
    required_font_markers=("GillSans", "Cambria", "Optima"),
)


def validate_source_profile(
    profile: SourceProfile,
    *,
    page_count: int,
    font_names: set[str],
) -> None:
    """Validate the basic source identity against a profile."""

    if page_count != profile.expected_page_count:
        raise SourceIdentityError(
            f"{profile.name} expects {profile.expected_page_count} pages, got {page_count}"
        )

    missing = [
        marker
        for marker in profile.required_font_markers
        if not any(marker in font_name for font_name in font_names)
    ]
    if missing:
        raise SourceIdentityError(
            f"{profile.name} missing expected font markers: {', '.join(missing)}"
        )
