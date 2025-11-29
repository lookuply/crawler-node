"""Tests for coordinator client."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from crawler_node.coordinator_client import CoordinatorClient


@pytest.fixture
def client() -> CoordinatorClient:
    """Create coordinator client."""
    return CoordinatorClient(base_url="http://test-coordinator:8000", api_version="v1")


@pytest.mark.asyncio
async def test_fetch_next_urls_success(client: CoordinatorClient) -> None:
    """Test fetching next URLs from coordinator."""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": 1,
            "url": "https://example.com",
            "priority": 5,
            "domain": "example.com",
            "status": "pending",
        }
    ]
    mock_response.raise_for_status = MagicMock()

    # Mock the client.get method
    client.client.get = AsyncMock(return_value=mock_response)

    tasks = await client.fetch_next_urls(limit=10)

    assert len(tasks) == 1
    assert tasks[0].id == 1
    assert tasks[0].url == "https://example.com"
    assert tasks[0].priority == 5


@pytest.mark.asyncio
async def test_fetch_next_urls_empty(client: CoordinatorClient) -> None:
    """Test fetching URLs when none available."""
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()

    client.client.get = AsyncMock(return_value=mock_response)

    tasks = await client.fetch_next_urls(limit=10)

    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_mark_crawling(client: CoordinatorClient) -> None:
    """Test marking URL as crawling."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    client.client.post = AsyncMock(return_value=mock_response)

    await client.mark_crawling(url_id=1)

    # Verify it was called
    client.client.post.assert_called_once()


@pytest.mark.asyncio
async def test_mark_completed(client: CoordinatorClient) -> None:
    """Test marking URL as completed."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    client.client.post = AsyncMock(return_value=mock_response)

    await client.mark_completed(url_id=1)

    # Verify it was called
    client.client.post.assert_called_once()


@pytest.mark.asyncio
async def test_mark_failed(client: CoordinatorClient) -> None:
    """Test marking URL as failed."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    client.client.post = AsyncMock(return_value=mock_response)

    await client.mark_failed(url_id=1, error_message="Test error")

    # Verify it was called with error_message
    client.client.post.assert_called_once()
    call_args = client.client.post.call_args
    assert call_args.kwargs["json"]["error_message"] == "Test error"


@pytest.mark.asyncio
async def test_connection_error(client: CoordinatorClient) -> None:
    """Test handling connection errors."""
    client.client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

    with pytest.raises(httpx.ConnectError):
        await client.fetch_next_urls(limit=10)
