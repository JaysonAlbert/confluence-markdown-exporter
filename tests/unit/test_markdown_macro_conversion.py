"""Unit tests for markdown macro conversion."""

from unittest.mock import patch

from bs4 import BeautifulSoup

from confluence_markdown_exporter.confluence import Page


class _MockPage:
    def __init__(self, editor2: str) -> None:
        self.id = 300679816
        self.title = "Test Page"
        self.html = ""
        self.body_export = ""
        self.editor2 = editor2
        self.labels = []
        self.ancestors = []
        self.attachments = []

    def get_attachment_by_file_id(self, file_id: str) -> None:  # noqa: ARG002
        return None

    def get_attachment_by_id(self, attachment_id: str) -> None:  # noqa: ARG002
        return None

    def get_attachments_by_title(self, title: str) -> list[None]:  # noqa: ARG002
        return []


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_fallback_to_single_editor2_macro_when_no_macro_id(mock_settings) -> None:
    """Extract markdown when view macro has no data-macro-id but editor2 has one macro."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[# Title
some **markdown** content
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)

    # Simulates problematic Confluence HTML where macro-id is missing in view body
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "# Title" in result
    assert "some **markdown** content" in result
    assert "content not found" not in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_fallback_to_rendered_view_text_when_editor2_empty(mock_settings) -> None:
    """Use rendered macro body when editor2 content is unavailable."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    page = _MockPage(editor2="")
    converter = Page.Converter(page)

    view_el = BeautifulSoup(
        '<div data-macro-name="markdown"><h1>SQL 用户维度分析报告</h1><p><strong>生成时间</strong>: now</p></div>',
        "html.parser",
    ).find("div")
    converted_text = converter.convert(str(view_el)).strip()

    result = converter.convert_markdown(view_el, converted_text, [])

    assert "SQL 用户维度分析报告" in result
    assert "**生成时间**" in result
    assert "content not found" not in result
