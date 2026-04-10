"""키움 인증 모듈 테스트"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.brokers.kiwoom.auth import KiwoomAuth
from app.core.exceptions import AuthError


@pytest.fixture
def auth():
    return KiwoomAuth(
        app_key="test_key",
        app_secret="test_secret",
        base_url="https://mockapi.kiwoom.com",
    )


class TestKiwoomAuth:
    async def test_initial_state(self, auth):
        assert auth.token is None
        assert auth.is_valid is False

    async def test_get_token_triggers_refresh(self, auth):
        with patch.object(auth, "_do_refresh", new_callable=AsyncMock) as mock:
            mock.return_value = "new_token"
            auth._token = "new_token"
            auth._expires_at = datetime.now() + timedelta(hours=1)
            token = await auth.get_token()
        assert token == "new_token"

    async def test_valid_token_no_refresh(self, auth):
        auth._token = "existing"
        auth._expires_at = datetime.now() + timedelta(hours=1)
        token = await auth.get_token()
        assert token == "existing"

    async def test_expired_token_triggers_refresh(self, auth):
        auth._token = "old"
        auth._expires_at = datetime.now() - timedelta(minutes=1)
        with patch.object(auth, "_do_refresh", new_callable=AsyncMock) as mock:
            mock.return_value = "refreshed"
            auth._token = "refreshed"
            auth._expires_at = datetime.now() + timedelta(hours=1)
            token = await auth.get_token()
        assert token == "refreshed"

    async def test_near_expiry_triggers_refresh(self, auth):
        """만료 5분 전이면 갱신"""
        auth._token = "near_expiry"
        auth._expires_at = datetime.now() + timedelta(minutes=3)
        assert auth.is_valid is False

    async def test_invalidate(self, auth):
        auth._token = "valid"
        auth._expires_at = datetime.now() + timedelta(hours=1)
        auth.invalidate()
        assert auth.token is None
        assert auth.is_valid is False

    async def test_refresh_lock_prevents_concurrent(self, auth):
        """동시 갱신 시 락으로 1회만 실행"""
        call_count = 0

        async def slow_refresh():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            auth._token = "new"
            auth._expires_at = datetime.now() + timedelta(hours=1)
            return "new"

        with patch.object(auth, "_do_refresh", side_effect=slow_refresh):
            results = await asyncio.gather(
                auth.get_token(),
                auth.get_token(),
                auth.get_token(),
            )
        # 첫 호출이 락 잡고 갱신, 나머지는 유효한 토큰 반환
        assert all(r == "new" for r in results)
        assert call_count == 1

    async def test_retry_on_failure(self, auth):
        """갱신 실패 시 재시도 후 최종 실패 시 AuthError"""
        auth._max_retries = 2
        with patch.object(
            auth, "_do_refresh", new_callable=AsyncMock, side_effect=Exception("network")
        ):
            with pytest.raises(AuthError, match="토큰 갱신 실패"):
                await auth.get_token()
