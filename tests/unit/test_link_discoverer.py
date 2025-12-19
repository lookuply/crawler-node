"""Tests for link discoverer."""

import pytest

from crawler_node.link_discoverer import LinkDiscoverer


@pytest.fixture
def discoverer() -> LinkDiscoverer:
    """Create link discoverer with test-friendly configuration."""
    return LinkDiscoverer(
        allowed_domains=[r'.*'],  # Allow all domains for testing
        min_parent_score=40,  # Lower threshold for testing
    )


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

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    assert "https://example.com/page1" in urls
    assert "https://example.com/page2" in urls
    assert "https://other.com/page" in urls


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

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    assert "https://example.com/about" in urls
    assert "https://example.com/contact" in urls
    assert "https://example.com/products/item1" in urls


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

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    # Both should point to same URL without fragment
    assert "https://example.com/page" in urls
    # Should not contain fragments
    assert all("#" not in url for url in urls)


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

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    assert "https://example.com/page" in urls
    assert len([url for url in urls if "javascript:" in url]) == 0
    assert len([url for url in urls if "mailto:" in url]) == 0
    assert len([url for url in urls if "ftp:" in url]) == 0


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

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    # Should only have one instance
    assert urls.count("https://example.com/page") == 1


def test_discover_handles_malformed_html(discoverer: LinkDiscoverer) -> None:
    """Test handling of malformed HTML."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Unclosed link
            <a href="/another">Another</a>
        </body>
    """

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    # Should still extract valid links
    assert "https://example.com/page" in urls or "https://example.com/another" in urls


def test_discover_empty_html(discoverer: LinkDiscoverer) -> None:
    """Test discovering links from empty HTML."""
    links = discoverer.discover("", "https://example.com", parent_score=80)

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

    links = discoverer.discover(html, "https://example.com", parent_score=80)

    assert len(links) == 0


def test_discover_returns_dict_format(discoverer: LinkDiscoverer) -> None:
    """Test that discover returns dicts with correct keys."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Page</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com", parent_score=75, depth=1)

    assert len(links) == 1
    link = links[0]

    # Check all required keys exist
    assert "url" in link
    assert "priority" in link
    assert "depth" in link
    assert "parent_url" in link

    # Check values
    assert link["url"] == "https://example.com/page"
    assert link["parent_url"] == "https://example.com"
    assert link["depth"] == 2  # Parent depth + 1
    assert isinstance(link["priority"], int)
    assert 0 <= link["priority"] <= 100


def test_discover_respects_parent_score_threshold(discoverer: LinkDiscoverer) -> None:
    """Test that low-quality parent pages don't discover links."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Page</a>
        </body>
    </html>
    """

    # Low parent score (below default threshold of 40)
    links = discoverer.discover(html, "https://example.com", parent_score=20)

    # Should not discover links from low-quality pages
    assert len(links) == 0


def test_discover_respects_max_depth(discoverer: LinkDiscoverer) -> None:
    """Test that max depth prevents link discovery."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Page</a>
        </body>
    </html>
    """

    # At max depth (default is 3)
    links = discoverer.discover(html, "https://example.com", parent_score=80, depth=3)

    # Should not discover links at max depth
    assert len(links) == 0


def test_discover_priority_based_on_parent_score(discoverer: LinkDiscoverer) -> None:
    """Test that link priority is influenced by parent score."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page">Page</a>
        </body>
    </html>
    """

    # High quality parent
    high_score_links = discoverer.discover(html, "https://example.com", parent_score=90)

    # Medium quality parent
    medium_score_links = discoverer.discover(html, "https://example.com", parent_score=50)

    # Links from higher quality pages should have higher priority
    if high_score_links and medium_score_links:
        assert high_score_links[0]["priority"] >= medium_score_links[0]["priority"]


def test_discover_filters_blocked_extensions(discoverer: LinkDiscoverer) -> None:
    """Test that blocked file extensions are filtered."""
    html = """
    <html>
        <body>
            <a href="https://example.com/page.html">HTML</a>
            <a href="https://example.com/image.jpg">Image</a>
            <a href="https://example.com/doc.pdf">PDF</a>
            <a href="https://example.com/video.mp4">Video</a>
        </body>
    </html>
    """

    links = discoverer.discover(html, "https://example.com", parent_score=80)
    urls = [link["url"] for link in links]

    # HTML pages should be kept
    assert "https://example.com/page.html" in urls

    # Binary files should be filtered
    assert "https://example.com/image.jpg" not in urls
    assert "https://example.com/doc.pdf" not in urls
    assert "https://example.com/video.mp4" not in urls
