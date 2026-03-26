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


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_adds_mermaid_language_for_plain_fence(mock_settings) -> None:
    """Infer mermaid language when fenced code has no language."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
sequenceDiagram
    participant A
    participant B
    A->>B: ping
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```mermaid" in result
    assert "sequenceDiagram" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_keeps_plain_fence_when_language_unknown(mock_settings) -> None:
    """Keep content even when language is uncertain."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
unknown syntax content
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "unknown syntax content" in result
    assert result.count("```") >= 2


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_adds_json_language_for_plain_fence(mock_settings) -> None:
    """Infer json language when fenced code contains valid JSON."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
{
  "errCode": "SUCCESS",
  "data": [{"id": 1}]
}
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```json" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_adds_sql_language_for_plain_fence(mock_settings) -> None:
    """Infer sql language for SQL snippets with comment headers."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
-- TITANS_MARGIN 数据源
SELECT a.KEY_PLAN_ID, b.*
FROM REF_BUSINESS_PLAN_TRADE_PARAM a
INNER JOIN MARGIN_PLAN_COMMISSION_PARAM b ON a.ID = b.KEY_TRADE_PARAM_ID
WHERE a.KEY_PLAN_ID IN (FICC部门所有方案IDs)
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```sql" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_normalizes_googlesql_to_sql(mock_settings) -> None:
    """Normalize sql-like fence aliases to sql."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```googlesql
CREATE TABLE T_DEMO (ID NUMBER);
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```sql" in result
    assert "```googlesql" not in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_normalizes_componentpascal_to_sql(mock_settings) -> None:
    """Normalize wrong lexer result componentpascal to sql."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```componentpascal
CREATE TABLE T_DEMO (ID NUMBER);
COMMENT ON TABLE T_DEMO IS 'demo';
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```sql" in result
    assert "```componentpascal" not in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_adds_sql_language_for_create_table_ddl(mock_settings) -> None:
    """Infer sql for Oracle-style CREATE TABLE DDL snippets."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
CREATE TABLE TITANS_DM.FICC_SOD_MGN_PLAN_COMM_PARAM (
    TRADE_DATE VARCHAR2(20) NOT NULL,
    KEY_PLAN_ID NUMBER NOT NULL
);
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```sql" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_adds_java_language_for_enum_constant_snippet(mock_settings) -> None:
    """Infer java for enum-style constant declarations."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
// FTDataType.java
FICC_MARGIN_PLAN_COMM_PARAM("FICC_MARGIN_PLAN_COMM_PARAM", "desc", "FICC_SOD_MGN_PLAN_COMM_PARAM"),
FICC_MARGIN_PLAN_INT_PARAM("FICC_MARGIN_PLAN_INT_PARAM", "desc", "FICC_SOD_MGN_PLAN_INT_PARAM")
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```java" in result


@patch("confluence_markdown_exporter.confluence.settings")
def test_convert_markdown_adds_http_language_for_endpoint_snippet(mock_settings) -> None:
    """Infer http for API endpoint examples."""
    mock_settings.export.include_document_title = False
    mock_settings.export.page_breadcrumbs = False

    editor2 = """<?xml version="1.0" encoding="UTF-8"?>
<ac:structured-macro ac:name="markdown" ac:macro-id="macro-1">
    <ac:plain-text-body><![CDATA[```
# 上场佣金费率参数
GET /ficc/data/sod?ftDataType=FICC_MARGIN_PLAN_COMM_PARAM

# 上场利息参数
GET /ficc/data/sod?ftDataType=FICC_MARGIN_PLAN_INT_PARAM
```
]]></ac:plain-text-body>
</ac:structured-macro>"""

    page = _MockPage(editor2=editor2)
    converter = Page.Converter(page)
    view_el = BeautifulSoup('<div data-macro-name="markdown"></div>', "html.parser").find("div")

    result = converter.convert_markdown(view_el, "", [])

    assert "```http" in result
