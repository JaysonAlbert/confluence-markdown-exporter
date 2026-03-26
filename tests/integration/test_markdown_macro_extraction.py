"""Integration test for markdown macro extraction against a real Confluence page."""

from __future__ import annotations

from typing import Any

import pytest
from atlassian import Confluence as ConfluenceApiSdk
from bs4 import BeautifulSoup

from confluence_markdown_exporter.confluence import Page
from confluence_markdown_exporter.utils.app_data_store import get_settings


class _IntegrationPage:
    """Minimal page object for Page.Converter integration testing."""

    def __init__(
        self,
        page_id: int,
        title: str,
        html: str,
        body_export: str,
        editor2: str,
    ) -> None:
        self.id = page_id
        self.title = title
        self.html = html
        self.body_export = body_export
        self.editor2 = editor2
        self.labels = []
        self.ancestors = []
        self.attachments = []

    def get_attachment_by_file_id(self, file_id: str) -> None:  # noqa: ARG002
        return None

    def get_attachment_by_id(self, attachment_id: str) -> None:  # noqa: ARG002
        return None

    def get_attachments_by_title(self, title: str) -> list[Any]:  # noqa: ARG002
        return []


def _build_real_confluence_client() -> Any:
    settings = get_settings()
    auth = settings.auth.confluence
    connection_config = settings.connection_config.model_dump(exclude={"use_v2_api"})
    return ConfluenceApiSdk(
        url=str(auth.url),
        username=auth.username.get_secret_value() if auth.api_token else None,
        password=auth.api_token.get_secret_value() if auth.api_token else None,
        token=auth.pat.get_secret_value() if auth.pat else None,
        **connection_config,
    )


def test_markdown_macro_extraction_real_page_300679816() -> None:
    """Reproduce markdown macro extraction warning with a real configured page."""
    page_id = 300679816
    try:
        confluence_client = _build_real_confluence_client()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Unable to create Confluence client from local config: {exc}")

    try:
        page_data = confluence_client.get_page_by_id(
            page_id, expand="body.view,body.export_view,body.editor2"
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Unable to fetch page {page_id}: {exc}")

    body_view = page_data.get("body", {}).get("view", {}).get("value", "")
    body_export = page_data.get("body", {}).get("export_view", {}).get("value", "")
    body_editor2 = page_data.get("body", {}).get("editor2", {}).get("value", "")
    page = _IntegrationPage(
        page_id=page_id,
        title=page_data.get("title", ""),
        html=body_view,
        body_export=body_export,
        editor2=body_editor2,
    )

    converter = Page.Converter(page)
    soup = BeautifulSoup(page.html, "html.parser")
    macros = soup.find_all(attrs={"data-macro-name": ["markdown", "mohamicorp-markdown"]})

    print(f"\npage_id={page_id}")
    print(f"view_len={len(body_view)} export_len={len(body_export)} editor2_len={len(body_editor2)}")
    print(f"markdown_macros_in_view={len(macros)}")

    if not macros:
        pytest.skip("No markdown macro found in page view body; cannot reproduce this issue.")

    missing_content_macro_ids: list[str] = []

    for idx, macro in enumerate(macros, start=1):
        macro_name = macro.get("data-macro-name", "")
        macro_id = macro.get("data-macro-id", "")
        macro_text = macro.get_text(strip=True)
        from_body = converter._extract_markdown_from_body(macro)
        from_editor2 = converter._extract_markdown_from_editor2(macro_id) if macro_id else None
        converted_text = converter.convert(str(macro)).strip()
        converted_macro = converter.convert_markdown(macro, converted_text, [])
        extracted = from_body or from_editor2 or converted_macro

        print(
            f"macro#{idx} name={macro_name} id={macro_id} "
            f"text_len={len(macro_text)} body_len={len(from_body or '')} "
            f"editor2_len={len(from_editor2 or '')} converted_len={len(converted_macro or '')}"
        )
        print(f"macro#{idx} attrs={dict(macro.attrs)}")
        print(f"macro#{idx} inner_html_snippet={str(macro)[:400]}")

        if not extracted or "content not found" in converted_macro:
            missing_content_macro_ids.append(str(macro_id))

    assert not missing_content_macro_ids, (
        "Markdown macro content extraction failed for macro IDs: "
        f"{missing_content_macro_ids}"
    )
