import logging
import os
from pathlib import Path
from typing import Annotated

import typer

from confluence_markdown_exporter import __version__
from confluence_markdown_exporter.utils.app_data_store import get_settings
from confluence_markdown_exporter.utils.app_data_store import set_setting
from confluence_markdown_exporter.utils.config_interactive import main_config_menu_loop
from confluence_markdown_exporter.utils.lockfile import LockfileManager
from confluence_markdown_exporter.utils.logging_config import setup_export_logging
from confluence_markdown_exporter.utils.measure_time import measure
from confluence_markdown_exporter.utils.platform_compat import handle_powershell_tilde_expansion
from confluence_markdown_exporter.utils.type_converter import str_to_bool

DEBUG: bool = str_to_bool(os.getenv("DEBUG", "False"))

app = typer.Typer()

_logger = logging.getLogger(__name__)


def override_output_path_config(value: Path | None) -> None:
    """Override the default output path if provided."""
    if value is not None:
        set_setting("export.output_path", value)


def _prepare_export_run(
    output_path: Path | None,
    log_file: Path | None,
) -> Path:
    """Apply output path override, attach file+stderr logging, return resolved log path."""
    override_output_path_config(output_path)
    settings = get_settings()
    resolved_log = (
        log_file
        if log_file is not None
        else (settings.export.output_path / "confluence-markdown-exporter.log")
    )
    setup_export_logging(resolved_log, debug=DEBUG)
    _logger.info("Writing logs to %s", resolved_log)
    return resolved_log


@app.command(help="Export one or more Confluence pages by ID or URL to Markdown.")
def pages(
    pages: Annotated[list[str], typer.Argument(help="Page ID(s) or URL(s)")],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(help="Log file path. Default: <export.output_path>/confluence-markdown-exporter.log"),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page
    from confluence_markdown_exporter.confluence import sync_removed_pages

    with measure(f"Export pages {', '.join(pages)}"):
        _prepare_export_run(output_path, log_file)
        LockfileManager.init()
        for page in pages:
            _page = None
            try:
                _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
                _page.export()
                LockfileManager.record_page(_page)
            except Exception:
                ref = _page.id if _page is not None else page
                _logger.exception(
                    "Export failed (Confluence page id or argument: %s)",
                    ref,
                )
                raise
        sync_removed_pages()


@app.command(help="Export Confluence pages and their descendant pages by ID or URL to Markdown.")
def pages_with_descendants(
    pages: Annotated[list[str], typer.Argument(help="Page ID(s) or URL(s)")],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(help="Log file path. Default: <export.output_path>/confluence-markdown-exporter.log"),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Page
    from confluence_markdown_exporter.confluence import sync_removed_pages

    with measure(f"Export pages {', '.join(pages)} with descendants"):
        _prepare_export_run(output_path, log_file)
        LockfileManager.init()
        for page in pages:
            _page = None
            try:
                _page = Page.from_id(int(page)) if page.isdigit() else Page.from_url(page)
                _page.export_with_descendants()
            except Exception:
                ref = _page.id if _page is not None else page
                _logger.exception(
                    "Export failed (Confluence page id or argument: %s)",
                    ref,
                )
                raise
        sync_removed_pages()


@app.command(help="Export all Confluence pages of one or more spaces to Markdown.")
def spaces(
    space_keys: Annotated[list[str], typer.Argument()],
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(help="Log file path. Default: <export.output_path>/confluence-markdown-exporter.log"),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Space
    from confluence_markdown_exporter.confluence import sync_removed_pages

    # Personal Confluence spaces start with ~. Exporting them on Windows leads to
    # Powershell expanding tilde to the Users directory, which is handled here
    normalized_space_keys = [handle_powershell_tilde_expansion(key) for key in space_keys]

    with measure(f"Export spaces {', '.join(normalized_space_keys)}"):
        _prepare_export_run(output_path, log_file)
        LockfileManager.init()
        for space_key in normalized_space_keys:
            space = Space.from_key(space_key)
            space.export()
        sync_removed_pages()


@app.command(help="Export all Confluence pages across all spaces to Markdown.")
def all_spaces(
    output_path: Annotated[
        Path | None,
        typer.Option(
            help="Directory to write exported Markdown files to. Overrides config if set."
        ),
    ] = None,
    log_file: Annotated[
        Path | None,
        typer.Option(help="Log file path. Default: <export.output_path>/confluence-markdown-exporter.log"),
    ] = None,
) -> None:
    from confluence_markdown_exporter.confluence import Organization
    from confluence_markdown_exporter.confluence import sync_removed_pages

    with measure("Export all spaces"):
        _prepare_export_run(output_path, log_file)
        LockfileManager.init()
        org = Organization.from_api()
        org.export()
        sync_removed_pages()


@app.command(help="Open the interactive configuration menu or display current configuration.")
def config(
    jump_to: Annotated[
        str | None,
        typer.Option(help="Jump directly to a config submenu, e.g. 'auth.confluence'"),
    ] = None,
    *,
    show: Annotated[
        bool,
        typer.Option(
            "--show",
            help="Display current configuration as YAML instead of opening the interactive menu",
        ),
    ] = False,
) -> None:
    """Interactive configuration menu or display current configuration."""
    if show:
        current_settings = get_settings()
        json_output = current_settings.model_dump_json(indent=2)
        typer.echo(f"```json\n{json_output}\n```")
    else:
        main_config_menu_loop(jump_to)


@app.command(help="Show the current version of confluence-markdown-exporter.")
def version() -> None:
    """Display the current version."""
    typer.echo(f"confluence-markdown-exporter {__version__}")


if __name__ == "__main__":
    app()
