"""Tests for robots.txt handler."""

from unittest.mock import AsyncMock

import pytest

from crawler_node.robots_handler import RobotsHandler


@pytest.fixture
def handler() -> RobotsHandler:
    """Create robots handler."""
    return RobotsHandler(user_agent="TestBot/1.0")


@pytest.mark.asyncio
async def test_can_fetch_allowed(handler: RobotsHandler) -> None:
    """Test URL is allowed by robots.txt."""
    # Mock robots.txt response
    robots_txt = """
User-agent: *
Disallow: /admin
Disallow: /private
Allow: /
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    result = await handler.can_fetch("https://example.com/page.html")

    assert result is True


@pytest.mark.asyncio
async def test_can_fetch_disallowed(handler: RobotsHandler) -> None:
    """Test URL is disallowed by robots.txt."""
    robots_txt = """
User-agent: *
Disallow: /admin
Disallow: /private
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    result = await handler.can_fetch("https://example.com/admin/users")

    assert result is False


@pytest.mark.asyncio
async def test_can_fetch_specific_user_agent(handler: RobotsHandler) -> None:
    """Test specific user agent rules."""
    robots_txt = """
User-agent: TestBot
Disallow: /test

User-agent: *
Allow: /
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    result = await handler.can_fetch("https://example.com/test/page")

    assert result is False


@pytest.mark.asyncio
async def test_can_fetch_no_robots_txt(handler: RobotsHandler) -> None:
    """Test when robots.txt doesn't exist (404)."""
    handler._fetch_robots = AsyncMock(return_value=None)

    # Should allow by default when no robots.txt
    result = await handler.can_fetch("https://example.com/page.html")

    assert result is True


@pytest.mark.asyncio
async def test_can_fetch_caches_robots_txt(handler: RobotsHandler) -> None:
    """Test that robots.txt is cached per domain."""
    robots_txt = """
User-agent: *
Disallow: /admin
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    # First call
    await handler.can_fetch("https://example.com/page1.html")

    # Second call to same domain
    await handler.can_fetch("https://example.com/page2.html")

    # Should only fetch robots.txt once
    assert handler._fetch_robots.call_count == 1


@pytest.mark.asyncio
async def test_get_crawl_delay_default(handler: RobotsHandler) -> None:
    """Test default crawl delay when not specified."""
    robots_txt = """
User-agent: *
Disallow: /admin
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    delay = await handler.get_crawl_delay("https://example.com")

    # Should return None when not specified
    assert delay is None


@pytest.mark.asyncio
async def test_get_crawl_delay_specified(handler: RobotsHandler) -> None:
    """Test crawl delay when specified in robots.txt."""
    robots_txt = """
User-agent: *
Crawl-delay: 5
Disallow: /admin
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    delay = await handler.get_crawl_delay("https://example.com")

    assert delay == 5.0


@pytest.mark.asyncio
async def test_get_crawl_delay_specific_user_agent(handler: RobotsHandler) -> None:
    """Test crawl delay for specific user agent."""
    robots_txt = """
User-agent: TestBot
Crawl-delay: 10

User-agent: *
Crawl-delay: 2
"""

    handler._fetch_robots = AsyncMock(return_value=robots_txt)

    delay = await handler.get_crawl_delay("https://example.com")

    assert delay == 10.0
