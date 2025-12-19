"""Main crawler orchestration."""

import asyncio
from collections.abc import AsyncGenerator

import httpx

from crawler_node.config import settings
from crawler_node.content_extractor import ContentExtractor, ExtractedContent
from crawler_node.coordinator_client import CoordinatorClient, CrawlTask
from crawler_node.link_discoverer import LinkDiscoverer
from crawler_node.robots_handler import RobotsHandler


class Crawler:
    """Main crawler that orchestrates crawling process."""

    def __init__(
        self,
        coordinator_url: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Initialize crawler.

        Args:
            coordinator_url: URL of coordinator API
            user_agent: User agent string to use
        """
        self.coordinator_url = coordinator_url or settings.coordinator_url
        self.user_agent = user_agent or settings.user_agent

        self.coordinator = CoordinatorClient(
            base_url=self.coordinator_url,
            api_version=settings.coordinator_api_version,
        )
        self.robots = RobotsHandler(user_agent=self.user_agent)
        self.extractor = ContentExtractor()
        self.discoverer = LinkDiscoverer()

        self.http_client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
        )

    async def crawl_task(self, task: CrawlTask) -> ExtractedContent | None:
        """Crawl a single URL task.

        Args:
            task: Crawl task from coordinator

        Returns:
            Extracted content or None if crawl failed
        """
        url = task.url

        try:
            # Mark as crawling
            await self.coordinator.mark_crawling(task.id)

            # Check robots.txt
            if settings.respect_robots_txt:
                can_fetch = await self.robots.can_fetch(url)
                if not can_fetch:
                    await self.coordinator.mark_failed(
                        task.id,
                        error_message="Disallowed by robots.txt",
                    )
                    return None

                # Respect crawl delay
                crawl_delay = await self.robots.get_crawl_delay(url)
                if crawl_delay:
                    await asyncio.sleep(crawl_delay)
                else:
                    await asyncio.sleep(settings.crawl_delay)

            # Fetch the page
            response = await self.http_client.get(url)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type.lower():
                await self.coordinator.mark_failed(
                    task.id,
                    error_message=f"Not HTML: {content_type}",
                )
                return None

            # Extract content
            html = response.text
            content = self.extractor.extract(html, url)

            if not content:
                await self.coordinator.mark_failed(
                    task.id,
                    error_message="Content extraction failed",
                )
                return None

            # Discover links (if enabled)
            if settings.extract_links:
                links = self.discoverer.discover(
                    html,
                    url,
                    parent_score=0,  # Will be updated when AI evaluation is integrated
                    depth=0,  # Will be updated when depth tracking is integrated
                )

                # Submit discovered links to coordinator
                if links:
                    try:
                        result = await self.coordinator.submit_discovered_links(
                            links=links[:100],  # Limit to 100 URLs (API max)
                            source_url=url,
                            priority=6,  # Slightly lower priority than manual submissions
                        )
                        print(f"Discovered {len(links)} links from {url}: "
                              f"{result['added']} new, {result['skipped']} duplicates")
                    except Exception as e:
                        print(f"Failed to submit {len(links)} links from {url}: {e}")

            # Submit content to coordinator for indexing (if long enough)
            if len(content.text) >= 50:
                try:
                    await self.coordinator.submit_content(
                        url_id=task.id,
                        title=content.title,
                        content=content.text,
                        language=content.language,
                        author=content.author,
                        date=content.date,  # date is already a string from trafilatura
                    )
                    print(f"Submitted content for {url} (title: {content.title or 'N/A'})")
                except Exception as e:
                    print(f"Warning: Failed to submit content for {url}: {e}")
            else:
                print(f"Skipping content submission for {url}: content too short ({len(content.text)} chars)")

            # Mark as completed
            await self.coordinator.mark_completed(task.id)

            return content

        except httpx.HTTPStatusError as e:
            await self.coordinator.mark_failed(
                task.id,
                error_message=f"HTTP {e.response.status_code}",
            )
            return None

        except httpx.RequestError as e:
            await self.coordinator.mark_failed(
                task.id,
                error_message=f"Request error: {str(e)}",
            )
            return None

        except Exception as e:
            await self.coordinator.mark_failed(
                task.id,
                error_message=f"Unexpected error: {str(e)}",
            )
            return None

    async def run(self, max_tasks: int = 100) -> AsyncGenerator[ExtractedContent]:
        """Run crawler continuously.

        Args:
            max_tasks: Maximum number of tasks to process

        Yields:
            Extracted content from crawled pages
        """
        tasks_processed = 0

        while tasks_processed < max_tasks:
            # Fetch next URLs from coordinator
            tasks = await self.coordinator.fetch_next_urls(
                limit=settings.max_concurrent_requests
            )

            if not tasks:
                # No more tasks available
                print("No tasks available, waiting...")
                await asyncio.sleep(5)
                continue

            # Process tasks concurrently
            results = await asyncio.gather(
                *[self.crawl_task(task) for task in tasks],
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, ExtractedContent):
                    tasks_processed += 1
                    yield result

    async def close(self) -> None:
        """Close all clients."""
        await self.http_client.aclose()
        await self.coordinator.close()
