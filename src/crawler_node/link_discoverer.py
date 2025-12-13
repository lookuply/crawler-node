"""Link discovery from HTML pages."""

import logging
from typing import Optional
from urllib.parse import urldefrag, urljoin, urlparse

from bs4 import BeautifulSoup

from crawler_node.constants import EU_LANGUAGES
from crawler_node.language_predictor import LanguagePredictor

logger = logging.getLogger(__name__)


class LinkDiscoverer:
    """Discoverer for extracting links from HTML."""

    def __init__(self, language_predictor: Optional[LanguagePredictor] = None) -> None:
        """Initialize link discoverer.

        Args:
            language_predictor: Language predictor for filtering (default: create new instance)
        """
        self.language_predictor = language_predictor or LanguagePredictor()

    def discover(
        self,
        html: str,
        base_url: str,
        same_domain_only: bool = False,
        filter_by_language: bool = True,
        allowed_languages: Optional[set[str]] = None,
    ) -> list[str]:
        """Discover links from HTML.

        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            same_domain_only: Only return links from same domain
            filter_by_language: Filter links by European languages (default: True)
            allowed_languages: Set of allowed language codes (default: EU_LANGUAGES)

        Returns:
            List of discovered URLs (filtered by language if enabled)
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

        # Apply language filtering if enabled
        if filter_by_language:
            links = self._filter_by_language(links, allowed_languages or EU_LANGUAGES)

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

    def _filter_by_language(self, links: set[str], allowed_languages: set[str]) -> set[str]:
        """Filter links by predicted language.

        Args:
            links: Set of URLs to filter
            allowed_languages: Set of allowed language codes (ISO 639-1)

        Returns:
            Filtered set of URLs (only EU languages + unknown)
        """
        filtered = set()
        stats = {"total": len(links), "kept": 0, "filtered": 0, "unknown": 0}

        for link in links:
            predicted_lang = self.language_predictor.predict(link)

            if predicted_lang is None:
                # Unknown language → keep (safe approach, avoid false positives)
                filtered.add(link)
                stats["unknown"] += 1
            elif predicted_lang == "SKIP":
                # Definitely non-EU → filter
                stats["filtered"] += 1
            elif predicted_lang in allowed_languages:
                # EU language → keep
                filtered.add(link)
                stats["kept"] += 1
            else:
                # Non-EU language → filter
                stats["filtered"] += 1

        # Log statistics
        if stats["total"] > 0:
            logger.info(
                f"Language filtering: {stats['kept']} kept ({stats['kept']/stats['total']*100:.1f}%), "
                f"{stats['filtered']} filtered ({stats['filtered']/stats['total']*100:.1f}%), "
                f"{stats['unknown']} unknown ({stats['unknown']/stats['total']*100:.1f}%) "
                f"out of {stats['total']} total links"
            )
        else:
            logger.info("Language filtering: no links to filter")

        return filtered
