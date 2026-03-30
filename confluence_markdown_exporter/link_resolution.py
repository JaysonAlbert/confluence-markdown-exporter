"""Helpers for resolving Confluence page links and fragments."""

from __future__ import annotations

import re
import urllib.parse

from bs4 import BeautifulSoup

from confluence_markdown_exporter.utils.export import sanitize_filename
from confluence_markdown_exporter.utils.export import sanitize_key


def extract_page_id_and_fragment_from_href(href: str | None) -> tuple[int | None, str | None]:
    """Extract a Confluence page ID and optional fragment from a page href."""
    if not href:
        return None, None

    parsed = urllib.parse.urlparse(str(href))
    path = parsed.path.rstrip("/")

    if match := re.search(r"/wiki/.+?/pages/(\d+)", path):
        return int(match.group(1)), parsed.fragment or None

    if "viewpage.action" in path:
        query = urllib.parse.parse_qs(parsed.query)
        page_ids = query.get("pageId") or query.get("pageid")
        if page_ids and page_ids[0].isdigit():
            return int(page_ids[0]), parsed.fragment or None

    return None, parsed.fragment or None


def normalize_confluence_anchor_fragment(
    fragment: str | None,
    *,
    page_title: str | None = None,
    page_body_html: str | None = None,
) -> str | None:
    """Convert a Confluence fragment into a Markdown heading anchor."""
    if not fragment:
        return None

    decoded = urllib.parse.unquote(fragment).lstrip("#").strip()
    if not decoded:
        return None

    if decoded.startswith("id-"):
        decoded = decoded[3:]
        if page_title:
            for prefix in (page_title, sanitize_filename(page_title)):
                prefix_with_sep = f"{prefix}-"
                if decoded.startswith(prefix_with_sep):
                    decoded = decoded[len(prefix_with_sep):]
                    break

    if page_body_html:
        fragment_lookup = re.sub(r"[\W_]+", "", decoded.casefold())
        if fragment_lookup:
            soup = BeautifulSoup(page_body_html, "html.parser")
            best_heading = None
            best_score = 0
            for heading in soup.find_all(re.compile(r"^h[1-6]$")):
                heading_text = heading.get_text(" ", strip=True)
                heading_lookup = re.sub(r"[\W_]+", "", heading_text.casefold())
                if not heading_lookup:
                    continue
                if heading_lookup == fragment_lookup:
                    return sanitize_key(heading_text, "-")
                score = 0
                if fragment_lookup in heading_lookup:
                    score = len(fragment_lookup)
                elif heading_lookup in fragment_lookup:
                    score = len(heading_lookup)
                if score > best_score:
                    best_score = score
                    best_heading = heading_text
            if best_heading:
                return sanitize_key(best_heading, "-")

    normalized = sanitize_key(decoded, "-")
    return normalized or None
