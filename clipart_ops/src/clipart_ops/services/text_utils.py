"""Helper xử lý text không phụ thuộc package ngoài."""

from __future__ import annotations

import re
import unicodedata


def slugify_text(value: str) -> str:
    """Chuyển text thành slug ASCII đơn giản."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return slug or "untitled"
