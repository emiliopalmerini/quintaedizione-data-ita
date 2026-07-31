from __future__ import annotations

import pytest

from scripts.parse_srd_v2.errors import SourceIdentityError
from scripts.parse_srd_v2.profiles import SRD_521_IT, validate_source_profile


def test_profile_validation_accepts_expected_page_count_and_fonts() -> None:
    validate_source_profile(
        SRD_521_IT,
        page_count=405,
        font_names={"ABCDEE+GillSans-SemiBold", "Cambria", "Optima-Regular"},
        checksum_sha256=SRD_521_IT.accepted_checksum_sha256,
    )


def test_profile_validation_rejects_page_count_mismatch() -> None:
    with pytest.raises(SourceIdentityError, match="expects 405 pages"):
        validate_source_profile(SRD_521_IT, page_count=1, font_names={"Cambria"})


def test_profile_validation_rejects_missing_font_markers() -> None:
    with pytest.raises(SourceIdentityError, match="missing expected font markers"):
        validate_source_profile(SRD_521_IT, page_count=405, font_names={"Helvetica"})


def test_profile_validation_rejects_checksum_mismatch() -> None:
    with pytest.raises(SourceIdentityError, match="checksum mismatch"):
        validate_source_profile(
            SRD_521_IT,
            page_count=405,
            font_names={"GillSans", "Cambria", "Optima"},
            checksum_sha256="wrong",
        )
