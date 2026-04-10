"""키움 REST 클라이언트 테스트"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.brokers.kiwoom.client import KiwoomClient
from app.core.exceptions import OrderError, RateLimitError


@pytest.fixture
def mock_auth():
    auth = MagicMock()
    auth.get_token = AsyncMock(return_value="test_token")
    auth.invalidate = MagicMock()
    return auth


@pytest.fixture
def mock_rate_limiter():
    rl = MagicMock()
    rl.acquire = AsyncMock()
    return rl


@pytest.fixture
def client(mock_auth, mock_rate_limiter):
    return KiwoomClient(mock_auth, mock_rate_limiter, "https://mockapi.kiwoom.com")


class TestKiwoomClient:
    async def test_successful_request(self, client, mock_auth, mock_rate_limiter):
        mock_resp = httpx.Response(200, json={"result": "ok"})
        with patch.object(client._http, "request", new_callable=AsyncMock, return_value=mock_resp):
            result = await client.request("POST", "/api/test", "tr001", {"key": "val"})
        assert result == {"result": "ok"}
        mock_rate_limiter.acquire.assert_awaited_once()
        mock_auth.get_token.assert_awaited_once()

    async def test_401_retries_with_new_token(self, client, mock_auth):
        resp_401 = httpx.Response(401, json={"error": "unauthorized"})
        resp_200 = httpx.Response(200, json={"result": "ok"})

        with patch.object(
            client._http, "request", new_callable=AsyncMock, side_effect=[resp_401, resp_200]
        ):
            result = await client.request("POST", "/api/test", "tr001")
        assert result == {"result": "ok"}
        mock_auth.invalidate.assert_called_once()

    async def test_429_raises_rate_limit_error(self, client):
        resp_429 = httpx.Response(429, text="Too Many Requests")
        with patch.object(client._http, "request", new_callable=AsyncMock, return_value=resp_429):
            with pytest.raises(RateLimitError):
                await client.request("POST", "/api/test", "tr001")

    async def test_500_raises_order_error(self, client):
        resp_500 = httpx.Response(500, text="Internal Server Error")
        with patch.object(client._http, "request", new_callable=AsyncMock, return_value=resp_500):
            with pytest.raises(OrderError, match="서버 오류"):
                await client.request("POST", "/api/test", "tr001")

    async def test_400_raises_order_error(self, client):
        resp_400 = httpx.Response(400, text="Bad Request")
        with patch.object(client._http, "request", new_callable=AsyncMock, return_value=resp_400):
            with pytest.raises(OrderError, match="요청 오류"):
                await client.request("POST", "/api/test", "tr001")
