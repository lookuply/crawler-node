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

    async def submit_content(
        self,
        url_id: int,
        title: str | None,
        content: str,
        language: str | None,
        author: str | None = None,
        date: str | None = None,
    ) -> dict:
        """Submit crawled page content to coordinator.

        Args:
            url_id: ID of URL
            title: Page title
            content: Main text content
            language: Language code (e.g., 'en', 'sk')
            author: Author name
            date: Publication date (ISO format)

        Returns:
            API response with content submission details

        Raises:
            httpx.HTTPError: If request fails
        """
        payload = {
            "title": title,
            "content": content,
            "language": language,
        }

        if author:
            payload["author"] = author
        if date:
            payload["date"] = date

        url = f"{self.base_url}/api/{self.api_version}/content/urls/{url_id}/content"
        response = await self.client.post(url, json=payload)
        if response.status_code != 201:
            print(f"Content submission failed for URL {url_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            print(f"Payload: {payload}")
        response.raise_for_status()
        return response.json()

    async def submit_discovered_links(
        self,
        links: list[str],
        source_url: str,
        priority: int = 6,
    ) -> dict[str, int]:
        """Submit discovered links to coordinator.

        Submits multiple URLs at once using the batch endpoint.
        URLs that already exist will be skipped automatically.

        Args:
            links: List of discovered URLs
            source_url: URL where links were found (for logging)
            priority: Priority for new URLs (default: 6, slightly lower than manual)

        Returns:
            Dict with counts: {added, skipped, total}

        Raises:
            httpx.HTTPError: If request fails
        """
        if not links:
            return {"added": 0, "skipped": 0, "total": 0}

        # Prepare batch request
        urls_data = {
            "urls": [{"url": link, "priority": priority} for link in links]
        }

        url = f"{self.base_url}/api/{self.api_version}/urls/batch"
        response = await self.client.post(url, json=urls_data)
        response.raise_for_status()

        result = response.json()
        return {
            "added": result["added"],
            "skipped": result["skipped"],
            "total": result["total"],
        }

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "CoordinatorClient":
        """Enter async context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context."""
        await self.close()
