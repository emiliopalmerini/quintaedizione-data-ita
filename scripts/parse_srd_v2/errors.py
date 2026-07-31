"""Parser v2 exception types."""

from __future__ import annotations


class ParseSRDError(Exception):
    """Base error for parser v2 failures."""


class DependencyUnavailable(ParseSRDError):
    """Raised when an optional runtime dependency is missing."""


class SourceIdentityError(ParseSRDError):
    """Raised when the source PDF does not match the expected profile."""


class BuildValidationError(ParseSRDError):
    """Raised when a complete build fails required quality gates."""


class UnsupportedStage(ParseSRDError):
    """Raised for contracted stages that are not implemented yet."""
