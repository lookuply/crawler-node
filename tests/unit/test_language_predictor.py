"""Tests for LanguagePredictor."""

import pytest

from crawler_node.constants import EU_LANGUAGES
from crawler_node.language_predictor import LanguagePredictor


@pytest.fixture
def predictor():
    """Fixture for LanguagePredictor instance."""
    return LanguagePredictor()


class TestTLDPrediction:
    """Test TLD-based language prediction."""

    def test_predict_from_tld_slovak(self, predictor):
        """Test Slovak TLD prediction."""
        assert predictor.predict("https://example.sk/page") == "sk"

    def test_predict_from_tld_german(self, predictor):
        """Test German TLD prediction."""
        assert predictor.predict("https://example.de/page") == "de"

    def test_predict_from_tld_austria(self, predictor):
        """Test Austrian TLD returns German."""
        assert predictor.predict("https://example.at/page") == "de"

    def test_predict_from_tld_czech(self, predictor):
        """Test Czech TLD prediction."""
        assert predictor.predict("https://example.cz/page") == "cs"

    def test_predict_from_tld_french(self, predictor):
        """Test French TLD prediction."""
        assert predictor.predict("https://example.fr/page") == "fr"

    def test_predict_from_tld_spanish(self, predictor):
        """Test Spanish TLD prediction."""
        assert predictor.predict("https://example.es/page") == "es"

    def test_predict_from_tld_italian(self, predictor):
        """Test Italian TLD prediction."""
        assert predictor.predict("https://example.it/page") == "it"

    def test_predict_from_tld_polish(self, predictor):
        """Test Polish TLD prediction."""
        assert predictor.predict("https://example.pl/page") == "pl"

    def test_predict_from_tld_dutch(self, predictor):
        """Test Dutch TLD prediction."""
        assert predictor.predict("https://example.nl/page") == "nl"

    def test_predict_from_tld_greek(self, predictor):
        """Test Greek TLD prediction."""
        assert predictor.predict("https://example.gr/page") == "el"

    def test_predict_from_tld_belgian_dutch(self, predictor):
        """Test Belgian TLD returns Dutch (primary)."""
        assert predictor.predict("https://example.be/page") == "nl"

    def test_predict_from_tld_eu(self, predictor):
        """Test EU TLD returns English (primary)."""
        assert predictor.predict("https://example.eu/page") == "en"


class TestPathPrediction:
    """Test path-based language prediction."""

    def test_predict_from_path_english(self, predictor):
        """Test English path prediction."""
        assert predictor.predict("https://example.com/en/page") == "en"

    def test_predict_from_path_german(self, predictor):
        """Test German path prediction."""
        assert predictor.predict("https://example.com/de/article") == "de"

    def test_predict_from_path_slovak(self, predictor):
        """Test Slovak path prediction."""
        assert predictor.predict("https://example.com/sk/news") == "sk"

    def test_predict_from_path_french(self, predictor):
        """Test French path prediction."""
        assert predictor.predict("https://example.com/fr/page") == "fr"

    def test_predict_from_path_with_locale(self, predictor):
        """Test path with locale (en-us) extracts language."""
        assert predictor.predict("https://example.com/en-us/page") == "en"

    def test_predict_from_path_trailing_slash(self, predictor):
        """Test path with trailing slash."""
        assert predictor.predict("https://example.com/de/") == "de"

    def test_predict_path_no_language(self, predictor):
        """Test path without language code."""
        # .com TLD → None (generic)
        assert predictor.predict("https://example.com/about") is None


class TestSubdomainPrediction:
    """Test subdomain-based language prediction."""

    def test_predict_from_subdomain_english(self, predictor):
        """Test English subdomain prediction."""
        assert predictor.predict("https://en.example.com/page") == "en"

    def test_predict_from_subdomain_german(self, predictor):
        """Test German subdomain prediction."""
        # Note: Can't use wikipedia.org as it's allowlisted (returns None)
        assert predictor.predict("https://de.example.org/page") == "de"

    def test_predict_from_subdomain_french(self, predictor):
        """Test French subdomain prediction."""
        assert predictor.predict("https://fr.example.org/page") == "fr"

    def test_predict_from_subdomain_slovak(self, predictor):
        """Test Slovak subdomain prediction."""
        assert predictor.predict("https://sk.news.com/article") == "sk"

    def test_predict_subdomain_not_language(self, predictor):
        """Test subdomain that's not a language code."""
        # "www" is not a language code, should fall through
        result = predictor.predict("https://www.example.com/page")
        assert result is None


class TestQueryParamPrediction:
    """Test query parameter language prediction."""

    def test_predict_from_query_lang(self, predictor):
        """Test ?lang= query parameter."""
        assert predictor.predict("https://example.com/page?lang=en") == "en"

    def test_predict_from_query_language(self, predictor):
        """Test ?language= query parameter."""
        assert predictor.predict("https://example.com/page?language=de") == "de"

    def test_predict_from_query_locale(self, predictor):
        """Test ?locale= query parameter."""
        assert predictor.predict("https://example.com/page?locale=sk") == "sk"

    def test_predict_query_with_other_params(self, predictor):
        """Test language query param with other params."""
        assert predictor.predict("https://example.com/page?id=123&lang=fr&sort=date") == "fr"


class TestAllowlistDomains:
    """Test allowlisted domains always return None (always crawl)."""

    def test_allowlist_wikipedia(self, predictor):
        """Test Wikipedia is allowlisted."""
        assert predictor.predict("https://wikipedia.org/wiki/Test") is None

    def test_allowlist_wikipedia_subdomain(self, predictor):
        """Test Wikipedia subdomain is allowlisted."""
        # Note: subdomain matching takes precedence, but since wikipedia.org is allowlisted,
        # it should return None before checking subdomain
        assert predictor.predict("https://en.wikipedia.org/wiki/Test") is None

    def test_allowlist_europa_eu(self, predictor):
        """Test europa.eu is allowlisted."""
        assert predictor.predict("https://europa.eu/page") is None

    def test_allowlist_bbc(self, predictor):
        """Test BBC is allowlisted."""
        assert predictor.predict("https://bbc.co.uk/news") is None

    def test_allowlist_guardian(self, predictor):
        """Test The Guardian is allowlisted."""
        assert predictor.predict("https://theguardian.com/article") is None


class TestNonEULanguages:
    """Test non-EU language detection."""

    def test_predict_japanese_tld(self, predictor):
        """Test Japanese TLD returns SKIP."""
        result = predictor.predict("https://example.jp/page")
        assert result == "SKIP"

    def test_predict_chinese_tld(self, predictor):
        """Test Chinese TLD returns SKIP."""
        result = predictor.predict("https://example.cn/page")
        assert result == "SKIP"

    def test_predict_korean_tld(self, predictor):
        """Test Korean TLD returns SKIP."""
        result = predictor.predict("https://example.kr/page")
        assert result == "SKIP"

    def test_predict_russian_tld(self, predictor):
        """Test Russian TLD returns SKIP."""
        result = predictor.predict("https://example.ru/page")
        assert result == "SKIP"

    def test_predict_us_tld(self, predictor):
        """Test US TLD returns SKIP."""
        result = predictor.predict("https://example.us/page")
        assert result == "SKIP"

    def test_predict_brazilian_tld(self, predictor):
        """Test Brazilian TLD returns SKIP."""
        result = predictor.predict("https://example.br/page")
        assert result == "SKIP"


class TestUnknownLanguage:
    """Test unknown language returns None (crawl it)."""

    def test_predict_generic_com(self, predictor):
        """Test generic .com without hints returns None."""
        result = predictor.predict("https://example.com/page")
        assert result is None

    def test_predict_generic_org(self, predictor):
        """Test generic .org without hints returns None."""
        result = predictor.predict("https://example.org/page")
        assert result is None

    def test_predict_generic_net(self, predictor):
        """Test generic .net without hints returns None."""
        result = predictor.predict("https://example.net/page")
        assert result is None

    def test_predict_io(self, predictor):
        """Test .io TLD without hints returns None."""
        result = predictor.predict("https://example.io/page")
        assert result is None


class TestEULanguageValidation:
    """Test that predicted EU languages are in EU_LANGUAGES set."""

    def test_all_predicted_languages_are_eu(self, predictor):
        """Test that all predicted languages (not None, not SKIP) are EU languages."""
        test_urls = [
            "https://example.sk/page",
            "https://example.de/page",
            "https://example.fr/page",
            "https://example.com/en/page",
            "https://de.example.org/page",
        ]

        for url in test_urls:
            result = predictor.predict(url)
            if result is not None and result != "SKIP":
                assert result in EU_LANGUAGES, f"Predicted language '{result}' for {url} not in EU_LANGUAGES"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_predict_with_port(self, predictor):
        """Test URL with port number."""
        assert predictor.predict("https://example.sk:8080/page") == "sk"

    def test_predict_with_fragment(self, predictor):
        """Test URL with fragment."""
        assert predictor.predict("https://example.de/page#section") == "de"

    def test_predict_uppercase_url(self, predictor):
        """Test URL with uppercase characters."""
        # URL parsing should handle case normalization
        result = predictor.predict("https://EXAMPLE.SK/PAGE")
        assert result == "sk"

    def test_predict_http_protocol(self, predictor):
        """Test HTTP (not HTTPS) URL."""
        assert predictor.predict("http://example.de/page") == "de"

    def test_predict_malformed_url(self, predictor):
        """Test malformed URL returns None (safe default)."""
        result = predictor.predict("not-a-url")
        assert result is None

    def test_predict_empty_url(self, predictor):
        """Test empty URL returns None."""
        result = predictor.predict("")
        assert result is None


class TestPriorityOrder:
    """Test prediction priority order (allowlist > TLD > subdomain > path > query)."""

    def test_allowlist_overrides_tld(self, predictor):
        """Test allowlist takes priority over TLD."""
        # wikipedia.org is allowlisted, should return None even though .org is generic
        assert predictor.predict("https://wikipedia.org/test") is None

    def test_tld_overrides_generic(self, predictor):
        """Test TLD takes priority over generic .com."""
        # Even with .com, should still detect /de/ path
        assert predictor.predict("https://example.com/de/page") == "de"

    def test_subdomain_takes_priority_over_path(self, predictor):
        """Test subdomain takes priority over path when both present."""
        # Subdomain "fr" should be detected first
        result = predictor.predict("https://fr.example.com/de/page")
        # According to implementation order: TLD → subdomain → path
        # Since .com is generic (None), subdomain "fr" should be detected
        assert result == "fr"
