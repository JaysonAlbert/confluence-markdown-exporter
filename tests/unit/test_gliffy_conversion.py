"""Unit tests for Gliffy diagram conversion."""

from pathlib import Path
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from confluence_markdown_exporter.confluence import Ancestor
from confluence_markdown_exporter.confluence import Attachment
from confluence_markdown_exporter.confluence import Page
from confluence_markdown_exporter.confluence import Space
from confluence_markdown_exporter.confluence import User
from confluence_markdown_exporter.confluence import Version


def _build_space() -> Space:
    return Space(key="TEST", name="Test Space", description="", homepage=None)


def _build_version() -> Version:
    return Version(
        number=1,
        by=User(
            account_id="",
            username="",
            display_name="",
            public_name="",
            email="",
        ),
        when="",
        friendly_when="",
    )


def _build_attachment(title: str, media_type: str, comment: str = "", file_id: str = "") -> Attachment:
    return Attachment(
        id=file_id or title,
        title=title,
        space=_build_space(),
        file_size=1,
        media_type=media_type,
        media_type_description=media_type,
        file_id=file_id,
        collection_name="attachments",
        download_link="",
        comment=comment,
        ancestors=[],
        version=_build_version(),
    )


class _MockPage:
    def __init__(self, attachments: list[Attachment]) -> None:
        self.id = 171099740
        self.title = "任务93执行过慢原因定位"
        self.html = ""
        self.body = ""
        self.body_export = ""
        self.editor2 = ""
        self.labels = []
        self.space = _build_space()
        self.ancestors = [
            Ancestor(
                id=1,
                title="Parent",
                space=self.space,
                ancestors=[],
                version=_build_version(),
            )
        ]
        self.attachments = attachments
        self.export_path = Path("TEST/Home/任务93执行过慢原因定位.md")

    @property
    def _template_vars(self) -> dict[str, str]:
        return {
            "space_key": "TEST",
            "space_name": "Test Space",
            "homepage_id": "",
            "homepage_title": "",
            "ancestor_ids": "1",
            "ancestor_titles": "Parent",
        }

    def get_attachment_by_file_id(self, file_id: str) -> Attachment | None:
        for attachment in self.attachments:
            if attachment.file_id == file_id:
                return attachment
        return None

    def get_attachment_by_id(self, attachment_id: str) -> Attachment | None:
        for attachment in self.attachments:
            if attachment.id == attachment_id:
                return attachment
        return None

    def get_attachments_by_title(self, title: str) -> list[Attachment]:
        return [attachment for attachment in self.attachments if attachment.title == title]


@pytest.mark.parametrize(
    ("media_type", "comment", "expected_extension"),
    [
        ("application/gliffy+json", "", ".gliffy.json"),
        ("image/png", "gliffy preview", ".gliffy.png"),
    ],
)
def test_gliffy_attachment_extensions(
    media_type: str,
    comment: str,
    expected_extension: str,
) -> None:
    attachment = _build_attachment("diagram", media_type, comment=comment)
    assert attachment.extension == expected_extension


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_gliffy_uses_preview_and_source_links(mock_settings) -> None:
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False
    mock_settings.export.attachment_href = "relative"
    mock_settings.export.attachment_path = "{page_parent_path}/{attachment_file_id}{attachment_extension}"

    source = _build_attachment("日终估值任务调度", "application/gliffy+json", file_id="172099485")
    preview = _build_attachment(
        "日终估值任务调度.png",
        "image/png",
        comment="gliffy preview",
        file_id="172099486",
    )
    page = _MockPage([source, preview])
    converter = Page.Converter(page)

    html = '<div data-macro-name="gliffy">|diagramName=日终估值任务调度|</div>'
    el = BeautifulSoup(html, "html.parser").find("div")

    result = converter.convert_gliffy(el, "", [])

    assert "![日终估值任务调度](172099486.gliffy.png)" in result
    assert "](172099485.gliffy.json)" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_gliffy_falls_back_to_source_link_when_preview_missing(mock_settings) -> None:
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False
    mock_settings.export.attachment_href = "relative"
    mock_settings.export.attachment_path = "{page_parent_path}/{attachment_file_id}{attachment_extension}"

    source = _build_attachment("跨境估值任务调度", "application/gliffy+json", file_id="172099498")
    page = _MockPage([source])
    converter = Page.Converter(page)

    html = '<div data-macro-name="gliffy">|diagramName=跨境估值任务调度|</div>'
    el = BeautifulSoup(html, "html.parser").find("div")

    result = converter.convert_gliffy(el, "", [])

    assert "[跨境估值任务调度](172099498.gliffy.json)" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_gliffy_falls_back_to_rendered_img_when_attachment_is_unknown(mock_settings) -> None:
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False
    mock_settings.export.attachment_href = "relative"
    mock_settings.export.attachment_path = "{page_parent_path}/{attachment_file_id}{attachment_extension}"

    page = _MockPage([])
    converter = Page.Converter(page)

    html = (
        '<div data-macro-name="gliffy">'
        '<img src="/download/attachments/171099740/%E6%97%A5%E7%BB%88%E4%BC%B0%E5%80%BC.png" />'
        "</div>"
    )
    el = BeautifulSoup(html, "html.parser").find("div")

    result = converter.convert_gliffy(el, "", [])

    assert "![日终估值](/download/attachments/171099740/%E6%97%A5%E7%BB%88%E4%BC%B0%E5%80%BC.png)" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_span_gliffy_container_uses_gliffy_conversion(mock_settings) -> None:
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False
    mock_settings.export.attachment_href = "relative"
    mock_settings.export.attachment_path = "{page_parent_path}/{attachment_file_id}{attachment_extension}"

    source = _build_attachment("日终估值任务调度", "application/gliffy+json", file_id="172099485")
    preview = _build_attachment(
        "日终估值任务调度.png",
        "image/png",
        comment="gliffy preview",
        file_id="172099486",
    )
    page = _MockPage([source, preview])
    converter = Page.Converter(page)

    html = (
        '<span class="gliffy-container conf-macro output-inline" '
        'data-filename="日终估值任务调度">'
        '<img class="gliffy-image" alt="日终估值任务调度" '
        'src="/download/attachments/171099740/%E6%97%A5%E7%BB%88%E4%BC%B0%E5%80%BC.png" />'
        "</span>"
    )
    el = BeautifulSoup(html, "html.parser").find("span")

    result = converter.convert_span(el, "", [])

    assert "![日终估值任务调度](172099486.gliffy.png)" in result
    assert "](172099485.gliffy.json)" in result
