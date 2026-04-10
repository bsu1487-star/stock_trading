from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx

from app.core.constants import PATH_AUTH, TR_AUTH
from app.core.exceptions import AuthError
from app.monitoring.logger import get_logger

log = get_logger("kiwoom.auth")


class KiwoomAuth:
    """키움 OAuth 토큰 관리. 선제적 갱신, 갱신 락, 실패 재시도."""

    def __init__(self, app_key: str, app_secret: str, base_url: str):
        self._app_key = app_key
        self._app_secret = app_secret
        self._base_url = base_url
        self._token: str | None = None
        self._expires_at: datetime | None = None
        self._refresh_lock = asyncio.Lock()
        self._max_retries = 3

    @property
    def token(self) -> str | None:
        return self._token

    @property
    def is_valid(self) -> bool:
        return self._is_token_valid()

    def _is_token_valid(self) -> bool:
        if not self._token or not self._expires_at:
            return False
        return datetime.now() < self._expires_at - timedelta(minutes=5)

    async def get_token(self) -> str:
        """유효한 토큰 반환. 만료 임박 시 선제적 갱신."""
        if self._is_token_valid():
            return self._token
        return await self._refresh_token()

    async def _refresh_token(self) -> str:
        async with self._refresh_lock:
            # 락 획득 후 재확인
            if self._is_token_valid():
                return self._token

            last_error = None
            for attempt in range(self._max_retries):
                try:
                    return await self._do_refresh()
                except Exception as e:
                    last_error = e
                    log.warning(
                        "token_refresh_retry",
                        attempt=attempt + 1,
                        max_retries=self._max_retries,
                        error=str(e),
                    )
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(2**attempt)

            raise AuthError(f"토큰 갱신 실패 ({self._max_retries}회 재시도 후): {last_error}")

    async def _do_refresh(self) -> str:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            resp = await client.post(
                PATH_AUTH,
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._app_key,
                    "secretkey": self._app_secret,
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("return_code") != 0:
            raise AuthError(f"키움 인증 오류: {data.get('return_msg', data)}")

        self._token = data["token"]
        # expires_dt: "20260411224932" 형태
        expires_dt = data.get("expires_dt", "")
        if expires_dt:
            self._expires_at = datetime.strptime(expires_dt, "%Y%m%d%H%M%S")
        else:
            self._expires_at = datetime.now() + timedelta(hours=24)

        log.info("token_refreshed", expires_at=self._expires_at.isoformat())
        return self._token

    def invalidate(self):
        """토큰 강제 무효화 (401 응답 시 사용)"""
        self._token = None
        self._expires_at = None
