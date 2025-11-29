"""Content extraction from HTML pages."""

from dataclasses import dataclass
import trafilatura
from trafilatura.settings import use_config


@dataclass
class ExtractedContent:
    """Extracted content from a web page."""

    url: str
    title: str | None
    text: str
    language: str | None
    author: str | None = None
    date: str | None = None


class ContentExtractor:
    """Extractor for web page content."""

    def __init__(self) -> None:
        """Initialize content extractor."""
        # Configure trafilatura for optimal extraction
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")

    def extract(self, html: str, url: str) -> ExtractedContent | None:
        """Extract content from HTML.

        Args:
            html: Raw HTML content
            url: URL of the page

        Returns:
            Extracted content or None if extraction failed
        """
        if not html or not html.strip():
            return None

        # Extract using trafilatura
        extracted = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
            favor_recall=True,
            config=self.config,
            output_format="txt",
            with_metadata=True,
        )

        if not extracted:
            return None

        # Get metadata
        metadata = trafilatura.extract_metadata(html, default_url=url)

        # Extract title
        title = None
        if metadata and metadata.title:
            title = metadata.title

        # Extract language
        language = None
        if metadata and metadata.language:
            language = metadata.language

        # Extract author
        author = None
        if metadata and metadata.author:
            author = metadata.author

        # Extract date
        date = None
        if metadata and metadata.date:
            date = metadata.date

        # Filter out very short extractions (likely failed)
        if len(extracted) < 50:
            return None

        return ExtractedContent(
            url=url,
            title=title,
            text=extracted,
            language=language,
            author=author,
            date=date,
        )
