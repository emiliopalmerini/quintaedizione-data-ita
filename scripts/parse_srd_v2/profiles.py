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
    accepted_checksum_sha256: str | None = None


SRD_521_IT = SourceProfile(
    name="srd-5.2.1-it",
    source_id="srd-5.2.1-it",
    title="System Reference Document 5.2.1 Italiano",
    expected_page_count=405,
    required_font_markers=("GillSans", "Cambria", "Optima"),
    accepted_checksum_sha256=(
        "a7b88b0cd4f6424624cf5046c96755652985a27a2d405e30948e44b1f5e1f718"
    ),
)


def validate_source_profile(
    profile: SourceProfile,
    *,
    page_count: int,
    font_names: set[str],
    checksum_sha256: str | None = None,
) -> None:
    """Validate the basic source identity against a profile."""

    if page_count != profile.expected_page_count:
        raise SourceIdentityError(
            f"{profile.name} expects {profile.expected_page_count} pages, got {page_count}"
        )

    if (
        profile.accepted_checksum_sha256 is not None
        and checksum_sha256 is not None
        and checksum_sha256 != profile.accepted_checksum_sha256
    ):
        raise SourceIdentityError(f"{profile.name} checksum mismatch")

    missing = [
        marker
        for marker in profile.required_font_markers
        if not any(marker in font_name for font_name in font_names)
    ]
    if missing:
        raise SourceIdentityError(
            f"{profile.name} missing expected font markers: {', '.join(missing)}"
        )
