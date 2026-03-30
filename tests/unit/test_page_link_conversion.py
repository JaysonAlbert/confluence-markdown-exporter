"""Unit tests for Confluence page link conversion."""

from pathlib import Path
from unittest.mock import patch

from confluence_markdown_exporter.confluence import Page


class _MockPage:
    def __init__(self, *, title: str, export_path: str, body_export: str = "") -> None:
        self.id = 300068271
        self.title = title
        self.html = ""
        self.body = ""
        self.body_export = body_export
        self.editor2 = ""
        self.labels = []
        self.ancestors = []
        self.attachments = []
        self.export_path = Path(export_path)

    def get_attachment_by_file_id(self, file_id: str) -> None:  # noqa: ARG002
        return None

    def get_attachment_by_id(self, attachment_id: str) -> None:  # noqa: ARG002
        return None

    def get_attachments_by_title(self, title: str) -> list[None]:  # noqa: ARG002
        return []


@patch("confluence_markdown_exporter.confluence.settings")
@patch("confluence_markdown_exporter.confluence.Page.from_id")
def test_convert_server_page_link_to_relative_markdown_href(
    mock_from_id,
    mock_settings,
) -> None:
    """Convert Confluence Server pageId links into relative Markdown file links."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False
    mock_settings.export.page_href = "relative"

    source_page = _MockPage(
        title="一站通：支持自动拆分功能",
        export_path="自研投资管理系统/source/source.md",
    )
    linked_page = _MockPage(
        title="一站通：支持按合约平仓、compo港股通",
        export_path="自研投资管理系统/target/一站通：支持按合约平仓、compo港股通-265318887.md",
        body_export=(
            "<h1>一站通：支持按合约平仓、compo港股通</h1>"
            "<h3>2.10.1 AirBagX买入流水，交易品种为【深港通、沪港通】时簿记合约的跨币种类型、"
            "汇率模式等字段相应调整（250103版本）</h3>"
        ),
    )
    mock_from_id.return_value = linked_page

    converter = Page.Converter(source_page)
    html = (
        '<a href="http://wiki.gf.com.cn/pages/viewpage.action?pageId=265318887'
        '#id-%E4%B8%80%E7%AB%99%E9%80%9A%EF%BC%9A%E6%94%AF%E6%8C%81%E6%8C%89%E5%90%88%E7'
        '%BA%A6%E5%B9%B3%E4%BB%93%E3%80%81compo%E6%B8%AF%E8%82%A1%E9%80%9A-2.10.1AirBagX'
        '%E4%B9%B0%E5%85%A5%E6%B5%81%E6%B0%B4%EF%BC%8C%E4%BA%A4%E6%98%93%E5%93%81%E7%A7%'
        '8D%E4%B8%BA%E3%80%90%E6%B7%B1%E6%B8%AF%E9%80%9A%E3%80%81%E6%B2%AA%E6%B8%AF%E9%80'
        '%9A%E3%80%91%E6%97%B6%E7%B0%BF%E8%AE%B0%E5%90%88%E7%BA%A6%E7%9A%84%E8%B7%A8%E5%B8'
        '%81%E7%A7%8D%E7%B1%BB%E5%9E%8B%E3%80%81%E6%B1%87%E7%8E%87%E6%A8%A1%E5%BC%8F%E7%AD'
        '%89%E5%AD%97%E6%AE%B5%E7%9B%B8%E5%BA%94%E8%B0%83%E6%95%B4%EF%BC%88250103%E7%89%88'
        '%E6%9C%AC%EF%BC%89">'
        "参考文档</a>"
    )

    result = converter.convert(html).strip()

    assert (
        result
        == "[一站通：支持按合约平仓、compo港股通](../target/一站通：支持按合约平仓、compo港股通-265318887.md#key-2-10-1-airbagx-250103)"
    )


@patch("confluence_markdown_exporter.confluence.Page.from_id")
def test_from_url_supports_server_viewpage_action_links(mock_from_id) -> None:
    """Parse Confluence Server /pages/viewpage.action URLs by pageId."""
    Page.from_url("/pages/viewpage.action?pageId=265318887#id-something")

    mock_from_id.assert_called_once_with(265318887)
