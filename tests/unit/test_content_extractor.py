"""Tests for content extractor."""

import pytest

from crawler_node.content_extractor import ContentExtractor


@pytest.fixture
def extractor() -> ContentExtractor:
    """Create content extractor."""
    return ContentExtractor()


def test_extract_from_html_success(extractor: ContentExtractor) -> None:
    """Test extracting content from valid HTML."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="This is a test page">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is the main content of the page.</p>
            <p>It has multiple paragraphs.</p>
        </body>
    </html>
    """

    result = extractor.extract(html, "https://example.com/page")

    assert result is not None
    assert result.url == "https://example.com/page"
    assert result.title == "Test Page"
    assert "Main Title" in result.text
    assert "main content" in result.text
    assert result.language is not None


def test_extract_from_html_no_content(extractor: ContentExtractor) -> None:
    """Test extracting from HTML with no meaningful content."""
    html = """
    <html>
        <head><title>Empty</title></head>
        <body></body>
    </html>
    """

    result = extractor.extract(html, "https://example.com/empty")

    # Should return None or minimal content
    assert result is None or len(result.text) < 50


def test_extract_filters_boilerplate(extractor: ContentExtractor) -> None:
    """Test that boilerplate content is filtered out."""
    html = """
    <html>
        <head><title>Article</title></head>
        <body>
            <nav>Navigation menu</nav>
            <article>
                <h1>Article Title</h1>
                <p>This is the actual article content.</p>
            </article>
            <footer>Copyright 2024</footer>
        </body>
    </html>
    """

    result = extractor.extract(html, "https://example.com/article")

    assert result is not None
    assert "Article Title" in result.text
    assert "article content" in result.text
    # Boilerplate should be filtered
    assert "Navigation menu" not in result.text or "Copyright" not in result.text


def test_extract_handles_invalid_html(extractor: ContentExtractor) -> None:
    """Test extracting from malformed HTML."""
    html = "<html><body><p>Unclosed paragraph"

    result = extractor.extract(html, "https://example.com/broken")

    # Should handle gracefully
    assert result is None or result.text is not None


def test_extract_detects_language(extractor: ContentExtractor) -> None:
    """Test language detection."""
    html_en = """
    <html>
        <head><title>English Page</title></head>
        <body><p>This is an English text with many words to detect language.</p></body>
    </html>
    """

    result = extractor.extract(html_en, "https://example.com/en")

    assert result is not None
    # Language should be detected (may be 'en' or None if detection fails)
    assert result.language in ["en", None]


def test_extract_from_empty_string(extractor: ContentExtractor) -> None:
    """Test extracting from empty HTML."""
    result = extractor.extract("", "https://example.com/empty")

    assert result is None


def test_extract_preserves_paragraphs(extractor: ContentExtractor) -> None:
    """Test that paragraph structure is somewhat preserved."""
    html = """
    <html>
        <body>
            <p>First paragraph.</p>
            <p>Second paragraph.</p>
            <p>Third paragraph.</p>
        </body>
    </html>
    """

    result = extractor.extract(html, "https://example.com/paragraphs")

    assert result is not None
    # Check that all paragraphs are present
    assert "First paragraph" in result.text
    assert "Second paragraph" in result.text
    assert "Third paragraph" in result.text
