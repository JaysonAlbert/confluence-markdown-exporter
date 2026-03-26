"""Utility helpers for markdown fenced code language detection."""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

_MERMAID_KEYWORDS = {
    "graph",
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "journey",
    "gantt",
    "pie",
    "mindmap",
    "timeline",
    "quadrantChart",
    "requirementDiagram",
    "gitGraph",
    "packet-beta",
    "block-beta",
}

_FENCE_PATTERN = re.compile(r"(^|\n)```([^\n`]*)\n(.*?)(\n```)", flags=re.DOTALL)
_SQL_LANGUAGE_ALIASES = {
    "sql",
    "postgresql",
    "mysql",
    "tsql",
    "plsql",
    "googlesql",
    "componentpascal",
}

_HTTP_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS")


def _is_likely_sql(code_block_content: str) -> bool:
    """Heuristic check for SQL snippets."""
    normalized = code_block_content.strip().lower()
    if not normalized:
        return False

    sql_signals = (
        "select ",
        " from ",
        " where ",
        " join ",
        " group by ",
        " order by ",
        "insert into ",
        "update ",
        "delete from ",
        "create table ",
        "alter table ",
        "drop table ",
    )

    strong_sql_signals = (
        "create table ",
        "comment on table ",
    )
    if any(signal in normalized for signal in strong_sql_signals):
        return True

    oracle_ddl_signals = (
        " varchar2(",
        " number",
        " not null",
        " constraint ",
        " primary key",
    )
    if sum(1 for signal in oracle_ddl_signals if signal in normalized) >= 2:
        return True

    signal_count = sum(1 for signal in sql_signals if signal in normalized)
    return signal_count >= 2


def _is_likely_java(code_block_content: str) -> bool:
    """Heuristic check for Java snippets."""
    normalized = code_block_content.strip()
    lowered = normalized.lower()
    if not lowered:
        return False

    java_signals = (
        "public class ",
        "private class ",
        "enum ",
        "implements ",
        "extends ",
        "import java.",
        "package ",
        "public static final ",
    )
    if any(signal in lowered for signal in java_signals):
        return True

    # Common Java enum constant style with constructor call
    return bool(re.search(r"\b[A-Z][A-Z0-9_]*\s*\(\s*\"", normalized))


def _is_likely_http(code_block_content: str) -> bool:
    """Heuristic check for HTTP/API request snippets."""
    lines = [line.strip() for line in code_block_content.splitlines() if line.strip()]
    if not lines:
        return False

    request_lines = 0
    for line in lines:
        line_upper = line.upper()
        if any(line_upper.startswith(f"{method} /") for method in _HTTP_METHODS):
            request_lines += 1
    return request_lines >= 1


def _guess_fence_language(code_block_content: str) -> str:
    """Best-effort language detection for markdown code fences."""
    first_non_empty_line = ""
    for line in code_block_content.splitlines():
        stripped = line.strip()
        if stripped:
            first_non_empty_line = stripped
            break

    if first_non_empty_line in _MERMAID_KEYWORDS:
        return "mermaid"

    for keyword in _MERMAID_KEYWORDS:
        if first_non_empty_line.startswith(f"{keyword} "):
            return "mermaid"

    stripped_content = code_block_content.strip()
    if stripped_content.startswith("{") or stripped_content.startswith("["):
        try:
            json.loads(stripped_content)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            return "json"

    if _is_likely_sql(code_block_content):
        return "sql"
    if _is_likely_java(code_block_content):
        return "java"
    if _is_likely_http(code_block_content):
        return "http"
    return ""


def enrich_fenced_code_language(markdown_content: str, page_id: int) -> str:
    """Add missing fenced code languages when they can be inferred."""

    def replace(match: re.Match[str]) -> str:
        existing_language = match.group(2).strip().lower()
        code_content = match.group(3)

        if existing_language:
            if existing_language in _SQL_LANGUAGE_ALIASES and existing_language != "sql":
                return f"{match.group(1)}```sql\n{code_content}{match.group(4)}"
            if existing_language == "scdoc" and _is_likely_sql(code_content):
                return f"{match.group(1)}```sql\n{code_content}{match.group(4)}"
            return match.group(0)

        language = _guess_fence_language(code_content)
        if not language:
            snippet = code_content.strip().splitlines()
            snippet_preview = "\n".join(snippet[:5])
            logger.warning(
                "Unable to detect language for fenced code block in markdown macro "
                "(page_id=%s). Snippet:\n%s",
                page_id,
                snippet_preview,
            )
            return match.group(0)
        return f"{match.group(1)}```{language}\n{code_content}{match.group(4)}"

    return _FENCE_PATTERN.sub(replace, markdown_content)
