"""Unit tests for confluence module export_pages logic."""

from unittest.mock import MagicMock
from unittest.mock import patch

from confluence_markdown_exporter.confluence import export_pages


def test_export_pages_parallel() -> None:
    """Test export_pages utilizes parallel download execution."""
    mock_page_1 = MagicMock()
    mock_page_1.id = 1
    mock_page_2 = MagicMock()
    mock_page_2.id = 2

    pages = [mock_page_1, mock_page_2]

    with patch("confluence_markdown_exporter.confluence.LockfileManager") as mock_lockfile_mgr, \
         patch("confluence_markdown_exporter.confluence.Page.from_id") as mock_from_id, \
         patch("confluence_markdown_exporter.confluence.settings") as mock_settings:
        
        mock_lockfile_mgr.should_export.return_value = True
        
        mock_page_instance = MagicMock()
        mock_from_id.return_value = mock_page_instance
        
        # Enable parallel path
        mock_settings.export.parallel_downloads = 2
        
        export_pages(pages)
        
        mock_lockfile_mgr.mark_seen.assert_called_once_with([1, 2])
        assert mock_from_id.call_count == 2
        assert mock_page_instance.export.call_count == 2
        assert mock_lockfile_mgr.record_page.call_count == 2


def test_export_pages_serial() -> None:
    """Test export_pages utilizes sequential download execution."""
    mock_page_1 = MagicMock()
    mock_page_1.id = 3

    pages = [mock_page_1]

    with patch("confluence_markdown_exporter.confluence.LockfileManager") as mock_lockfile_mgr, \
         patch("confluence_markdown_exporter.confluence.Page.from_id") as mock_from_id, \
         patch("confluence_markdown_exporter.confluence.settings") as mock_settings:
        
        mock_lockfile_mgr.should_export.return_value = True
        
        mock_page_instance = MagicMock()
        mock_from_id.return_value = mock_page_instance
        
        # Enforce serial path
        mock_settings.export.parallel_downloads = 1
        
        export_pages(pages)
        
        mock_lockfile_mgr.mark_seen.assert_called_once_with([3])
        assert mock_from_id.call_count == 1
        assert mock_page_instance.export.call_count == 1
        assert mock_lockfile_mgr.record_page.call_count == 1
