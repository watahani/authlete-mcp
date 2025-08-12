"""Tests for description filtering functionality in models/base.py."""

import pytest

from src.authlete_mcp.models.base import DescriptionStyle, filter_description


class TestDescriptionFiltering:
    """Test description filtering functionality."""

    @pytest.fixture
    def sample_description(self):
        """Sample description with headers and content."""
        return """This is a comprehensive OAuth 2.0 authorization endpoint that handles client authentication.

The endpoint supports various authentication flows including authorization code and PKCE.

## Parameters

### Required Parameters
- client_id: The client identifier
- response_type: The response type (code, token, id_token)

### Optional Parameters
- redirect_uri: The redirection URI
- scope: The requested scopes

## Response Formats

The endpoint returns different response formats based on the request.

### Success Response
200 OK with authorization code

### Error Responses
400 Bad Request for invalid parameters
401 Unauthorized for authentication failures

## Security Considerations

This endpoint implements PKCE by default for public clients.

**Important**: Always validate redirect URIs to prevent attacks."""

    def test_filter_description_none_style(self, sample_description):
        """Test filtering with 'none' style."""
        result = filter_description(sample_description, DescriptionStyle.NONE)
        assert result is None

        result = filter_description(sample_description, "none")
        assert result is None

    def test_filter_description_full_style(self, sample_description):
        """Test filtering with 'full' style."""
        result = filter_description(sample_description, DescriptionStyle.FULL)
        assert result == sample_description

        result = filter_description(sample_description, "full")
        assert result == sample_description

    def test_filter_description_summary_and_headers_style(self, sample_description):
        """Test filtering with 'summary_and_headers' style."""
        result = filter_description(sample_description, DescriptionStyle.SUMMARY_AND_HEADERS)

        # Should contain summary section
        assert "=== Summary ===" in result
        assert "comprehensive OAuth 2.0 authorization endpoint" in result
        assert "supports various authentication flows" in result

        # Should contain headers section with line numbers
        assert "=== Headers ===" in result
        assert ": ## Parameters" in result
        assert ": ### Required Parameters" in result
        assert ": ### Optional Parameters" in result
        assert ": ## Response Formats" in result
        assert ": ### Success Response" in result
        assert ": ### Error Responses" in result
        assert ": ## Security Considerations" in result

        # Note: **Important** appears after the last ## header, so it won't be captured
        # as it's part of content, not a standalone header

        # Should NOT contain the full parameter descriptions
        assert "The client identifier" not in result
        assert "200 OK with authorization code" not in result

    def test_filter_description_line_range_style(self, sample_description):
        """Test filtering with 'line_range' style."""
        # Test specific line range (lines 1-5)
        result = filter_description(sample_description, DescriptionStyle.LINE_RANGE, (1, 5))

        lines = result.split("\n")
        assert len(lines) == 5
        assert lines[0].startswith("   1: ")
        assert lines[4].startswith("   5: ")
        assert "comprehensive OAuth 2.0 authorization endpoint" in result

        # Test with string style and range
        result = filter_description(sample_description, "line_range", (3, 7))
        lines = result.split("\n")
        assert len(lines) == 5  # Lines 3-7
        assert lines[0].startswith("   3: ")
        assert lines[4].startswith("   7: ")

    def test_filter_description_line_range_invalid_range(self, sample_description):
        """Test line range with invalid parameters."""
        # Start line greater than total lines
        result = filter_description(sample_description, "line_range", (1000, 1005))
        assert "Invalid line range: 1000-" in result and "(total lines:" in result

        # End line before start line
        result = filter_description(sample_description, "line_range", (10, 5))
        assert "Invalid line range: 10-5" in result

    def test_filter_description_line_range_no_range_specified(self, sample_description):
        """Test line range style without range specification."""
        result = filter_description(sample_description, "line_range", None)
        # Should return full description if no range specified
        assert result == sample_description

    def test_filter_description_empty_input(self):
        """Test filtering with empty or None input."""
        assert filter_description(None, DescriptionStyle.FULL) is None
        assert filter_description("", DescriptionStyle.SUMMARY_AND_HEADERS) == ""
        assert filter_description(None, "none") is None

    def test_filter_description_invalid_style(self, sample_description):
        """Test filtering with invalid style."""
        # Invalid enum should return full description
        result = filter_description(sample_description, "invalid_style")
        assert result == sample_description

    def test_filter_description_no_headers(self):
        """Test filtering text without headers."""
        text_without_headers = """This is a simple description without any headers.

It has multiple paragraphs but no markdown headers or bold headers.

This should be handled gracefully by the summary_and_headers style."""

        result = filter_description(text_without_headers, "summary_and_headers")

        # Should contain summary - when no headers, it includes the full text
        assert "=== Summary ===" in result
        assert "simple description without any headers" in result
        # Result will be longer due to "=== Summary ===" prefix, so check content preservation
        assert "multiple paragraphs" in result

    def test_filter_description_only_headers(self):
        """Test filtering text that starts with headers."""
        text_with_headers = """## First Header

Content under first header.

### Subheader

More content here.

## Second Header

Final content."""

        result = filter_description(text_with_headers, "summary_and_headers")

        # Should not have summary section (starts with header)
        assert "=== Summary ===" not in result

        # Should contain headers section
        assert "=== Headers ===" in result
        assert ": ## First Header" in result
        assert ": ### Subheader" in result
        assert ": ## Second Header" in result

        # Should not contain content
        assert "Content under first header" not in result
        assert "More content here" not in result

    def test_filter_description_mixed_header_formats(self):
        """Test filtering text with both markdown and bold headers."""
        mixed_text = """Initial summary text here.

## Markdown Header

Some content.

**Bold Header**

More content.

### Another Markdown Header

Final content."""

        result = filter_description(mixed_text, "summary_and_headers")

        # Should have both summary and headers
        assert "=== Summary ===" in result
        assert "Initial summary text here" in result

        assert "=== Headers ===" in result
        assert ": ## Markdown Header" in result
        assert ": **Bold Header**" in result
        assert ": ### Another Markdown Header" in result

        # Should not include content after headers
        assert "Some content" not in result
        assert "More content" not in result

    def test_filter_description_large_content_optimization(self):
        """Test that filtering significantly reduces content size."""
        # Create a large description with lots of content
        large_description = (
            """This is the summary section.

## Section 1

"""
            + "This is detailed content. " * 100
            + """

### Subsection 1.1

"""
            + "More detailed content here. " * 50
            + """

## Section 2

"""
            + "Even more content in this section. " * 75
            + """

### Subsection 2.1
### Subsection 2.2

"""
            + "Final detailed content. " * 60
        )

        original_size = len(large_description)
        filtered = filter_description(large_description, "summary_and_headers")
        filtered_size = len(filtered)

        # Should be significantly smaller (should be less than 20% of original)
        reduction_ratio = filtered_size / original_size
        assert reduction_ratio < 0.2, f"Expected >80% reduction, got {(1 - reduction_ratio) * 100:.1f}%"

        # But should still contain all the essential structure
        assert "=== Summary ===" in filtered
        assert "=== Headers ===" in filtered
        assert ": ## Section 1" in filtered
        assert ": ### Subsection 1.1" in filtered
        assert ": ## Section 2" in filtered
        assert ": ### Subsection 2.1" in filtered
        assert ": ### Subsection 2.2" in filtered
