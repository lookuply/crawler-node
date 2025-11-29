"""Main entry point for crawler node."""

import asyncio
import sys

from crawler_node.config import settings
from crawler_node.crawler import Crawler


async def main() -> None:
    """Run the crawler."""
    print("Starting Lookuply Crawler Node")
    print(f"Coordinator: {settings.coordinator_url}")
    print(f"User-Agent: {settings.user_agent}")
    print(f"Respect robots.txt: {settings.respect_robots_txt}")
    print("-" * 60)

    crawler = Crawler()

    try:
        async for content in crawler.run(max_tasks=1000):
            print(f"✓ Crawled: {content.url}")
            print(f"  Title: {content.title}")
            print(f"  Text length: {len(content.text)} chars")
            print(f"  Language: {content.language}")
            print()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await crawler.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
