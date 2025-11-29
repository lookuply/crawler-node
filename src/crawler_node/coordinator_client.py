"""Client for communicating with the coordinator."""

import httpx
from pydantic import BaseModel


class CrawlTask(BaseModel):
    """Crawl task from coordinator."""

    id: int
    url: str
    priority: int
    domain: str
    status: str


class CoordinatorClient:
    """Client for coordinator API."""

    def __init__(self, base_url: str, api_version: str = "v1") -> None:
        """Initialize coordinator client.

        Args:
            base_url: Base URL of coordinator
            api_version: API version to use
        """
        self.base_url = base_url.rstrip("/")
        self.api_version = api_version
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_next_urls(self, limit: int = 10) -> list[CrawlTask]:
        """Fetch next URLs to crawl from coordinator.

        Args:
            limit: Maximum number of URLs to fetch

        Returns:
            List of crawl tasks

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/api/{self.api_version}/urls"
        params = {"limit": limit}

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return [CrawlTask(**item) for item in data]

    async def mark_crawling(self, url_id: int) -> None:
        """Mark URL as being crawled.

        Args:
            url_id: ID of URL to mark

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/api/{self.api_version}/urls/{url_id}/crawling"
        response = await self.client.post(url)
        response.raise_for_status()

    async def mark_completed(self, url_id: int) -> None:
        """Mark URL as completed.

        Args:
            url_id: ID of URL to mark

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/api/{self.api_version}/urls/{url_id}/completed"
        response = await self.client.post(url)
        response.raise_for_status()

    async def mark_failed(self, url_id: int, error_message: str) -> None:
        """Mark URL as failed.

        Args:
            url_id: ID of URL to mark
            error_message: Error message

        Raises:
            httpx.HTTPError: If request fails
        """
        url = f"{self.base_url}/api/{self.api_version}/urls/{url_id}/failed"
        json_data = {"error_message": error_message}
        response = await self.client.post(url, json=json_data)
        response.raise_for_status()

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "CoordinatorClient":
        """Enter async context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context."""
        await self.close()
