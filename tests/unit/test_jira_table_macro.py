import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from confluence_markdown_exporter.confluence import Page

def test_jira_table_macro_cursor(
    temp_config_dir, sample_config_model, mock_confluence_client, confluence_space_response, caplog
):
    fixture_path = Path(__file__).parent.parent / "fixtures" / "jira_table_macro_issue.json"
    with open(fixture_path) as f:
        data = json.load(f)

    from confluence_markdown_exporter.confluence import Space, JiraIssue, User, Version
    import logging
    
    with patch("confluence_markdown_exporter.confluence.settings", sample_config_model), \
         patch("confluence_markdown_exporter.confluence.Space.from_key", return_value=Space(key="TEST", name="Test", description="", homepage=0)), \
         patch("confluence_markdown_exporter.confluence.Attachment.from_page_id", return_value=[]), \
         patch("confluence_markdown_exporter.confluence.User.from_json", return_value=User(account_id="test", username="test", display_name="test", email="test@test.com", public_name="test")), \
         patch("confluence_markdown_exporter.confluence.Version.from_json", return_value=Version(number=1, when="", friendly_when="", by=User(account_id="test", username="test", display_name="test", email="test@test.com", public_name="test"), message="", minorEdit=False)), \
         patch("confluence_markdown_exporter.confluence.JiraIssue.from_key", return_value=JiraIssue(key="TEST-123", summary="Test", description="Test", status="Open")), \
         patch("confluence_markdown_exporter.confluence.Page.from_id", return_value=Page(id=1, title="Ancestor", space=Space(key="A", name="A", description="", homepage=0), body="", body_export="", labels=[], attachments=[], ancestors=[], version=Version(number=1, when="", friendly_when="", by=User(account_id="test", username="test", display_name="test", email="", public_name="test"), message="", minorEdit=False), editor2="")):
        page = Page.from_json(data)
        
        # Monkeypatch convert_jira_table to see how many times it is called
        original_convert = page.Converter.convert_jira_table
        call_count = [0]
        
        def mock_convert_jira_table(self, el, text, parent_tags):
            call_count[0] += 1
            return original_convert(self, el, text, parent_tags)
            
        page.Converter.convert_jira_table = mock_convert_jira_table

        
        # Enable logging to capture warnings
        caplog.set_level(logging.WARNING)
        
        # Prevent actually writing to disk by mocking save_file
        with patch("confluence_markdown_exporter.confluence.save_file"):
            markdown = page.export_markdown()
            
            # Assert that the warning is NO LONGER emitted, confirming the fix
            assert "Could not map Jira table for macro instance. Ignoring." not in caplog.text, "Warning was still emitted!"
            
            # Also assert we called it the expected amount of times (due to table cell parsing duplicates this is > 18, but mapping handles it smoothly)
            assert call_count[0] > 18
            print("Successfully fixed warning.")
