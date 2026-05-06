"""Shared utility helpers for fluent_filepicker."""

from __future__ import annotations


def normalize_extensions(exts: list[str] | None) -> list[str]:
    """
    Normalize a list of file extensions to lowercase without leading dots.

    Args:
        exts: Raw extension list, e.g. [".PDF", "docx", ".PNG"], or None.

    Returns:
        Cleaned list, e.g. ["pdf", "docx", "png"].  Empty list if *exts* is
        None or empty.
    """
    if not exts:
        return []
    return [e.lower().lstrip(".") for e in exts]
