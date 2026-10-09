"""Common utility functions used across the application."""

from __future__ import annotations

import re
from datetime import datetime, timezone


def truncate_text(text: str, max_chars: int = 5000) -> str:
    """Truncate text to a maximum character count, preserving word boundaries."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "..."


def clean_html(raw_html: str) -> str:
    """Strip HTML tags and normalize whitespace from raw HTML content."""
    clean = re.sub(r"<script[^>]*>.*?</script>", "", raw_html, flags=re.DOTALL)
    clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token for English text)."""
    return max(1, len(text) // 4)


def build_citation(title: str, url: str, snippet: str = "") -> dict:
    """Build a structured citation object for a source.

    Args:
        title: Article or page title.
        url: Source URL.
        snippet: Optional text excerpt.

    Returns:
        Dictionary with citation metadata.
    """
    return {
        "title": title,
        "url": url,
        "snippet": truncate_text(snippet, 300) if snippet else "",
        "accessed_at": datetime.now(timezone.utc).isoformat(),
    }


def sanitize_filename(name: str) -> str:
    """Convert a string into a safe filename."""
    safe = re.sub(r"[^\w\s-]", "", name.lower())
    safe = re.sub(r"[-\s]+", "_", safe).strip("_")
    return safe[:100]


def format_report_timestamp() -> str:
    """Generate a human-readable timestamp string for reports."""
    return datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
