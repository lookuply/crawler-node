"""Language prediction from URL using heuristics.

Predicts language before crawling based on URL patterns, TLD, and domain allowlist.
Used for filtering non-EU language content at link discovery time.
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# TLD to language mapping (ccTLDs → primary language)
TLD_TO_LANGUAGES = {
    # Single-language EU countries
    "sk": ["sk"],  # Slovakia
    "cz": ["cs"],  # Czech Republic
    "de": ["de"],  # Germany
    "at": ["de"],  # Austria
    "fr": ["fr"],  # France
    "es": ["es"],  # Spain
    "it": ["it"],  # Italy
    "pl": ["pl"],  # Poland
    "nl": ["nl"],  # Netherlands
    "pt": ["pt"],  # Portugal
    "gr": ["el"],  # Greece
    "ro": ["ro"],  # Romania
    "bg": ["bg"],  # Bulgaria
    "hr": ["hr"],  # Croatia
    "hu": ["hu"],  # Hungary
    "lt": ["lt"],  # Lithuania
    "lv": ["lv"],  # Latvia
    "ee": ["et"],  # Estonia
    "fi": ["fi"],  # Finland
    "se": ["sv"],  # Sweden
    "dk": ["da"],  # Denmark
    "mt": ["mt"],  # Malta
    "si": ["sl"],  # Slovenia

    # Multi-language EU countries
    "be": ["nl", "fr"],  # Belgium
    "ie": ["en", "ga"],  # Ireland
    "lu": ["fr", "de"],  # Luxembourg
    "cy": ["el", "en"],  # Cyprus

    # EU institutions
    "eu": ["en", "de", "fr", "es"],

    # Non-EU but English-speaking
    "uk": ["en"],  # United Kingdom
    "gb": ["en"],  # Great Britain

    # Generic/international TLDs (check URL patterns)
    "com": None,
    "org": None,
    "net": None,
    "edu": None,
    "gov": None,
    "info": None,
    "biz": None,
    "io": None,
}

# Domains to always crawl (regardless of language prediction)
ALLOWLIST_DOMAINS = [
    # Wikipedia & Wikimedia
    "wikipedia.org",
    "wikimedia.org",
    "wikidata.org",
    "wikisource.org",
    "wiktionary.org",
    "wikiquote.org",
    "wikinews.org",

    # EU institutions
    "europa.eu",
    "europarl.europa.eu",
    "ec.europa.eu",
    "consilium.europa.eu",
    "european-union.europa.eu",

    # Major European news sites
    "bbc.co.uk",
    "bbc.com",
    "theguardian.com",
    "spiegel.de",
    "lemonde.fr",
    "elpais.es",
    "corriere.it",
    "reuters.com",
    "euronews.com",

    # Archive sites (preserve history)
    "archive.org",
    "web.archive.org",
]

# URL language patterns (regex for extracting language codes)
URL_LANGUAGE_PATTERNS = [
    # Path-based: /en/, /de/, /sk/
    (r"^/([a-z]{2})(?:/|$)", "path"),

    # Path-based with country: /en-us/, /de-de/, /pt-br/
    (r"^/([a-z]{2})-[a-z]{2}(?:/|$)", "path"),

    # Query parameter: ?lang=en, ?language=sk, ?locale=de
    (r"[?&](?:lang|language|locale)=([a-z]{2})", "query"),
]


class LanguagePredictor:
    """Predict language from URL using heuristics.

    Predicts language before crawling based on:
    - TLD (country code top-level domain)
    - URL path patterns (/en/, /de/)
    - Subdomain (en.example.com)
    - Query parameters (?lang=sk)
    - Domain allowlist (always crawl certain domains)

    Returns:
        - 2-letter ISO 639-1 code if EU language detected
        - None if language unknown (safe to crawl)
        - "SKIP" if definitely non-EU language
    """

    def __init__(self) -> None:
        """Initialize language predictor."""
        # Pre-compile regex patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern), source)
            for pattern, source in URL_LANGUAGE_PATTERNS
        ]

    def predict(self, url: str) -> Optional[str]:
        """Predict language from URL.

        Args:
            url: URL to analyze

        Returns:
            - 2-letter ISO code if EU language
            - None if unknown (crawl it)
            - "SKIP" if definitely non-EU
        """
        try:
            parsed = urlparse(url)

            # 1. Check allowlist domains → None (always crawl)
            if self._is_allowlisted(parsed.netloc):
                return None

            # 2. Check TLD
            tld = self._extract_tld(parsed.netloc)
            if tld in TLD_TO_LANGUAGES:
                langs = TLD_TO_LANGUAGES[tld]
                if langs:  # Not None
                    return langs[0]  # Return primary language
                # If None, continue to URL pattern checking

            # 3. Check subdomain (en.example.com, de.wikipedia.org)
            lang = self._extract_from_subdomain(parsed.netloc)
            if lang:
                return lang

            # 4. Check URL path patterns (/en/, /de/)
            lang = self._extract_from_path(parsed.path)
            if lang:
                return lang

            # 5. Check query parameters (?lang=sk)
            lang = self._extract_from_query(parsed.query)
            if lang:
                return lang

            # 6. Check for non-EU TLDs (Asian, etc.)
            if tld in self._get_non_eu_tlds():
                return "SKIP"

            # 7. Unknown language → None (keep it, crawl to be safe)
            return None

        except Exception as e:
            logger.warning(f"Error predicting language for {url}: {e}")
            return None  # Safe default: crawl it

    def _is_allowlisted(self, netloc: str) -> bool:
        """Check if domain is in allowlist.

        Args:
            netloc: Network location (domain)

        Returns:
            True if domain should always be crawled
        """
        # Remove port if present
        domain = netloc.split(":")[0].lower()

        # Check exact match or subdomain match
        for allowed_domain in ALLOWLIST_DOMAINS:
            if domain == allowed_domain or domain.endswith(f".{allowed_domain}"):
                return True

        return False

    def _extract_tld(self, netloc: str) -> Optional[str]:
        """Extract top-level domain from netloc.

        Args:
            netloc: Network location (domain)

        Returns:
            TLD (e.g., 'sk', 'com') or None
        """
        # Remove port if present
        domain = netloc.split(":")[0].lower()

        # Extract TLD (last part after final dot)
        parts = domain.split(".")
        if len(parts) >= 2:
            return parts[-1]

        return None

    def _extract_from_subdomain(self, netloc: str) -> Optional[str]:
        """Extract language from subdomain.

        Examples:
            en.wikipedia.org → 'en'
            de.example.com → 'de'

        Args:
            netloc: Network location (domain)

        Returns:
            2-letter language code or None
        """
        # Remove port if present
        domain = netloc.split(":")[0].lower()

        # Get first part (subdomain)
        parts = domain.split(".")
        if len(parts) >= 3:  # subdomain.example.com
            subdomain = parts[0]

            # Check if it's a 2-letter language code
            if len(subdomain) == 2 and subdomain.isalpha():
                return subdomain

        return None

    def _extract_from_path(self, path: str) -> Optional[str]:
        """Extract language from URL path.

        Examples:
            /en/page → 'en'
            /de-de/article → 'de'

        Args:
            path: URL path component

        Returns:
            2-letter language code or None
        """
        for pattern, _source in self.compiled_patterns:
            if _source == "path":
                match = pattern.search(path)
                if match:
                    lang = match.group(1).lower()
                    if len(lang) == 2 and lang.isalpha():
                        return lang

        return None

    def _extract_from_query(self, query: str) -> Optional[str]:
        """Extract language from query parameters.

        Examples:
            lang=en → 'en'
            language=sk → 'sk'

        Args:
            query: URL query string

        Returns:
            2-letter language code or None
        """
        for pattern, _source in self.compiled_patterns:
            if _source == "query":
                match = pattern.search(f"?{query}")
                if match:
                    lang = match.group(1).lower()
                    if len(lang) == 2 and lang.isalpha():
                        return lang

        return None

    def _get_non_eu_tlds(self) -> set[str]:
        """Get set of known non-EU TLDs to skip.

        Returns:
            Set of TLD codes to skip
        """
        return {
            # Asian TLDs
            "jp", "cn", "kr", "tw", "hk", "sg", "th", "my", "id", "ph", "vn",
            "in", "pk", "bd", "lk", "np", "mm", "kh", "la", "bn",

            # Middle Eastern TLDs
            "ae", "sa", "qa", "kw", "bh", "om", "ye", "jo", "lb", "sy", "iq", "il",

            # African TLDs (non-EU)
            "za", "eg", "ng", "ke", "tz", "ug", "gh", "ci", "sn", "ma", "tn",

            # American TLDs (non-EU)
            "us", "ca", "mx", "br", "ar", "cl", "co", "pe", "ve", "ec",

            # Oceanian TLDs
            "au", "nz", "pg", "fj", "nc",

            # Russian & CIS
            "ru", "ua", "by", "kz", "ge", "am", "az", "uz", "kg", "tj", "tm",

            # Other non-EU Europe
            "ch", "no", "is", "rs", "mk", "al", "ba", "me", "xk",
            "tr", "md",
        }
