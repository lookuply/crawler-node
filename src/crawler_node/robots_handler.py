"""Handler for robots.txt compliance."""

from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx


class RobotsHandler:
    """Handler for checking robots.txt compliance."""

    def __init__(self, user_agent: str = "Lookuply-Crawler/0.1.0") -> None:
        """Initialize robots handler.

        Args:
            user_agent: User agent string to use
        """
        self.user_agent = user_agent
        self._cache: dict[str, RobotFileParser] = {}

    async def _fetch_robots(self, url: str) -> str | None:
        """Fetch robots.txt for a domain.

        Args:
            url: URL to fetch robots.txt for

        Returns:
            robots.txt content or None if not found
        """
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    return response.text
                return None
        except (httpx.HTTPError, httpx.ConnectError):
            return None

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain (scheme + netloc)
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def _get_parser(self, url: str) -> RobotFileParser:
        """Get RobotFileParser for domain (cached).

        Args:
            url: URL to get parser for

        Returns:
            RobotFileParser instance
        """
        domain = self._get_domain(url)

        if domain not in self._cache:
            parser = RobotFileParser()
            robots_content = await self._fetch_robots(url)

            if robots_content:
                # Parse the robots.txt content
                parser.parse(robots_content.splitlines())
            else:
                # No robots.txt - allow everything
                parser.parse([])

            self._cache[domain] = parser

        return self._cache[domain]

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False otherwise
        """
        parser = await self._get_parser(url)
        return parser.can_fetch(self.user_agent, url)

    async def get_crawl_delay(self, url: str) -> float | None:
        """Get crawl delay for domain from robots.txt.

        Args:
            url: URL to get crawl delay for

        Returns:
            Crawl delay in seconds or None if not specified
        """
        parser = await self._get_parser(url)
        delay = parser.crawl_delay(self.user_agent)

        if delay is not None:
            return float(delay)
        return None

    def clear_cache(self) -> None:
        """Clear robots.txt cache."""
        self._cache.clear()
