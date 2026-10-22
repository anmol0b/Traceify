"""Helpers for putting untrusted, user-written text into prompts."""

from __future__ import annotations

# Prompts wrap scraped data in XML-style tags. Swapping angle brackets for look-alikes means a bio or
# tweet can't close a tag early (e.g. "</tweets>") and smuggle text outside the data block.
_ANGLE_BRACKETS = str.maketrans({"<": "‹", ">": "›"})


def data_safe(text: str | None) -> str:
    return (text or "").translate(_ANGLE_BRACKETS)
