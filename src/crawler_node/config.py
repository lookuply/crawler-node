"""Configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from crawler_node.constants import EU_LANGUAGES


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Coordinator settings
    coordinator_url: str = "http://localhost:8000"
    coordinator_api_version: str = "v1"

    # Crawler settings
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    user_agent: str = "Lookuply-Crawler/0.1.0 (+https://lookuply.info)"

    # Politeness settings
    respect_robots_txt: bool = True
    crawl_delay: float = 1.0  # seconds between requests to same domain

    # Content extraction
    extract_links: bool = True
    max_content_length: int = 10_000_000  # 10MB

    # Language filtering
    filter_by_language: bool = True
    allowed_languages: str = ",".join(EU_LANGUAGES)


settings = Settings()
