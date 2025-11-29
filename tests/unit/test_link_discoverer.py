"""Tests for link discoverer."""

import pytest

from crawler_node.link_discoverer import LinkDiscoverer


@pytest.fixture
def discoverer() -> LinkDiscoverer:
    """Create link discoverer."""
    return LinkDiscoverer()


def test_discover_absolute_links(discoverer: LinkDiscoverer) -> None:
    """Test discovering absolute URLs."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="https://other.com/page">Other</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com")

    assert "https://example.com/page1" in links
    assert "https://example.com/page2" in links
    assert "https://other.com/page" in links


def test_discover_relative_links(discoverer: LinkDiscoverer) -> None:
    """Test discovering relative URLs."""
    html = """
    <html>
        <body>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
            <a href="products/item1">Product</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com")

    assert "https://example.com/about" in links
    assert "https://example.com/contact" in links
    assert "https://example.com/products/item1" in links


def test_discover_filters_fragments(discoverer: LinkDiscoverer) -> None:
    """Test that URL fragments are removed."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page#section1">Section 1</a>
            <a href="https://example.com/page#section2">Section 2</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com")

    # Both should point to same URL without fragment
    assert "https://example.com/page" in links
    # Should not contain fragments
    assert all("#" not in link for link in links)


def test_discover_filters_invalid_schemes(discoverer: LinkDiscoverer) -> None:
    """Test that non-http(s) URLs are filtered."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Valid</a>
            <a href="javascript:void(0)">JavaScript</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="ftp://files.example.com">FTP</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com")

    assert "https://example.com/page" in links
    assert len([link for link in links if "javascript:" in link]) == 0
    assert len([link for link in links if "mailto:" in link]) == 0
    assert len([link for link in links if "ftp:" in link]) == 0


def test_discover_deduplicates_links(discoverer: LinkDiscoverer) -> None:
    """Test that duplicate links are removed."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Link 1</a>
            <a href="https://example.com/page">Link 2</a>
            <a href="https://example.com/page">Link 3</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com")

    # Should only have one instance
    assert links.count("https://example.com/page") == 1


def test_discover_handles_malformed_html(discoverer: LinkDiscoverer) -> None:
    """Test handling of malformed HTML."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Unclosed link
            <a href="/another">Another</a>
        </body>
    """

    links = discoverer.discover(html, "https://example.com")

    # Should still extract valid links
    assert "https://example.com/page" in links or "https://example.com/another" in links


def test_discover_empty_html(discoverer: LinkDiscoverer) -> None:
    """Test discovering links from empty HTML."""
    links = discoverer.discover("", "https://example.com")

    assert len(links) == 0


def test_discover_no_links(discoverer: LinkDiscoverer) -> None:
    """Test HTML with no links."""
    html = """
    <html>
        <body>
            <p>Just text, no links.</p>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com")

    assert len(links) == 0


def test_discover_same_domain_only(discoverer: LinkDiscoverer) -> None:
    """Test filtering to same domain only."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page1">Internal 1</a>
            <a href="https://example.com/page2">Internal 2</a>
            <a href="https://other.com/page">External</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com", same_domain_only=True)

    assert "https://example.com/page1" in links
    assert "https://example.com/page2" in links
    assert "https://other.com/page" not in links
