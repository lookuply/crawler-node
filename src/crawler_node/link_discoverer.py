"""Link discovery from HTML pages."""

from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup


class LinkDiscoverer:
    """Discoverer for extracting links from HTML."""

    def __init__(self) -> None:
        """Initialize link discoverer."""
        pass

    def discover(
        self,
        html: str,
        base_url: str,
        same_domain_only: bool = False,
    ) -> list[str]:
        """Discover links from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            same_domain_only: Only return links from same domain

        Returns:
            List of discovered URLs
        """
        if not html or not html.strip():
            return []

        soup = BeautifulSoup(html, "lxml")
        links = set()

        base_domain = self._get_domain(base_url)

        # Find all <a> tags with href
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Skip empty hrefs
            if not href or href.strip() == "":
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)

            # Remove fragment
            absolute_url, _ = urldefrag(absolute_url)

            # Filter invalid schemes
            if not self._is_valid_scheme(absolute_url):
                continue

            # Filter by domain if requested
            if same_domain_only:
                link_domain = self._get_domain(absolute_url)
                if link_domain != base_domain:
                    continue

            links.add(absolute_url)

        return list(links)

    def _is_valid_scheme(self, url: str) -> bool:
        """Check if URL has valid scheme.

        Args:
            url: URL to check

        Returns:
            True if scheme is http or https
        """
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"]

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain (netloc)
        """
        parsed = urlparse(url)
        return parsed.netloc
