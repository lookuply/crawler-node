"""Link discovery from HTML pages with quality-based filtering."""

import logging
import re
from typing import Optional
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Domain allowlist - only discover links from these domains
ALLOWED_DOMAINS = [
    r'.*\.wikipedia\.org$',
    r'.*\.wikimedia\.org$',
    r'docs\.python\.org$',
    r'developer\.mozilla\.org$',
    r'.*\.readthedocs\.io$',
    r'stackoverflow\.com$',
    r'github\.com$',
    r'arxiv\.org$',
]

# Blocked URL patterns (login, cart, API endpoints, pagination, etc.)
BLOCKED_PATTERNS = [
    r'/login', r'/register', r'/signup', r'/signin',
    r'/cart', r'/checkout', r'/admin',
    r'/api/', r'/rest/', r'/graphql',
    r'[?&]sort=', r'[?&]page=[2-9]', r'[?&]filter=',
    r'/edit', r'/delete', r'/remove',
]

# Blocked file extensions
BLOCKED_EXTENSIONS = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
    '.mp3', '.mp4', '.avi', '.mkv', '.mov',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.dylib',
]

# Crawl limits
MAX_DEPTH = 3
MIN_PARENT_SCORE = 60  # Only follow links from pages scoring 60+


class LinkDiscoverer:
    """Discovers links from HTML with quality-based filtering."""

    def __init__(
        self,
        allowed_domains: Optional[list[str]] = None,
        blocked_patterns: Optional[list[str]] = None,
        blocked_extensions: Optional[list[str]] = None,
        max_depth: int = MAX_DEPTH,
        min_parent_score: int = MIN_PARENT_SCORE
    ) -> None:
        """Initialize link discoverer.

        Args:
            allowed_domains: List of regex patterns for allowed domains
            blocked_patterns: List of regex patterns for blocked URL patterns
            blocked_extensions: List of blocked file extensions
            max_depth: Maximum crawl depth
            min_parent_score: Minimum parent AI score to follow links
        """
        self.allowed_domains = allowed_domains or ALLOWED_DOMAINS
        self.blocked_patterns = blocked_patterns or BLOCKED_PATTERNS
        self.blocked_extensions = blocked_extensions or BLOCKED_EXTENSIONS
        self.max_depth = max_depth
        self.min_parent_score = min_parent_score

    def discover(
        self,
        html: str,
        base_url: str,
        parent_score: int = 0,
        depth: int = 0
    ) -> list[dict]:
        """Discover links from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            parent_score: AI quality score of parent page (0-100)
            depth: Current crawl depth

        Returns:
            List of dicts with keys: url, priority, depth, parent_url
        """
        if not html or not html.strip():
            return []

        # Don't discover links from low-quality pages
        if parent_score < self.min_parent_score:
            logger.debug(
                f"Skipping link discovery: parent score {parent_score} < {self.min_parent_score}"
            )
            return []

        # Don't go deeper than max depth
        if depth >= self.max_depth:
            logger.debug(f"Skipping link discovery: depth {depth} >= {self.max_depth}")
            return []

        soup = BeautifulSoup(html, "lxml")
        discovered = []

        # Extract all links
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Skip empty hrefs
            if not href or href.strip() == "":
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)

            # Remove fragment
            absolute_url, _ = urldefrag(absolute_url)

            # Remove trailing slash
            absolute_url = absolute_url.rstrip('/')

            # Apply filtering rules
            if not self._should_crawl(absolute_url):
                continue

            # Calculate priority based on parent quality
            priority = self._calculate_priority(parent_score)

            discovered.append({
                'url': absolute_url,
                'priority': priority,
                'depth': depth + 1,
                'parent_url': base_url
            })

        # Deduplicate by URL
        seen = set()
        unique = []
        for item in discovered:
            if item['url'] not in seen:
                seen.add(item['url'])
                unique.append(item)

        logger.info(
            f"Discovered {len(unique)} unique links from {base_url} "
            f"(score={parent_score}, depth={depth})"
        )

        return unique

    def _should_crawl(self, url: str) -> bool:
        """Apply filtering rules to URL.

        Args:
            url: URL to check

        Returns:
            True if URL should be crawled
        """
        # Valid scheme check
        if not self._is_valid_scheme(url):
            return False

        # Domain allowlist check
        if not self._is_allowed_domain(url):
            return False

        # Pattern blocking check
        if self._is_blocked_pattern(url):
            return False

        # Extension blocking check
        if self._has_blocked_extension(url):
            return False

        return True

    def _is_valid_scheme(self, url: str) -> bool:
        """Check if URL has valid scheme.

        Args:
            url: URL to check

        Returns:
            True if scheme is http or https
        """
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"]

    def _is_allowed_domain(self, url: str) -> bool:
        """Check if domain is in allowlist.

        Args:
            url: URL to check

        Returns:
            True if domain matches any allowed pattern
        """
        domain = urlparse(url).netloc

        for pattern in self.allowed_domains:
            if re.match(pattern, domain):
                return True

        return False

    def _is_blocked_pattern(self, url: str) -> bool:
        """Check if URL matches blocked patterns.

        Args:
            url: URL to check

        Returns:
            True if URL matches any blocked pattern
        """
        for pattern in self.blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        return False

    def _has_blocked_extension(self, url: str) -> bool:
        """Check if URL has blocked file extension.

        Args:
            url: URL to check

        Returns:
            True if URL has blocked extension
        """
        path = urlparse(url).path.lower()

        for ext in self.blocked_extensions:
            if path.endswith(ext):
                return True

        return False

    def _calculate_priority(self, parent_score: int) -> str:
        """Calculate priority based on parent page quality.

        Args:
            parent_score: AI score of parent page (0-100)

        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        if parent_score >= 80:
            return 'high'
        elif parent_score >= 60:
            return 'medium'
        else:
            return 'low'
