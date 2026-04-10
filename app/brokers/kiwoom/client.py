from __future__ import annotations

import httpx

from app.core.exceptions import OrderError, RateLimitError
from app.monitoring.logger import get_logger

from .auth import KiwoomAuth
from .rate_limiter import RateLimiter

log = get_logger("kiwoom.client")


class KiwoomClient:
    """키움 REST API 공통 래퍼"""

    def __init__(
        self,
        auth: KiwoomAuth,
        rate_limiter: RateLimiter,
        base_url: str,
        app_key: str = "",
        app_secret: str = "",
    ):
        self._auth = auth
        self._rate_limiter = rate_limiter
        self._base_url = base_url
        self._app_key = app_key
        self._app_secret = app_secret
        self._http = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def request(
        self,
        method: str,
        path: str,
        tr_code: str,
        body: dict | None = None,
        *,
        retry_on_401: bool = True,
    ) -> dict:
        await self._rate_limiter.acquire()
        token = await self._auth.get_token()

        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {token}",
            "appkey": self._app_key,
            "secretkey": self._app_secret,
            "api-id": tr_code,
            "cont-yn": "N",
        }

        log.debug("api_request", method=method, path=path, tr_code=tr_code)

        resp = await self._http.request(method, path, headers=headers, json=body or {})

        if resp.status_code == 401 and retry_on_401:
            log.warning("token_expired_retry", path=path)
            self._auth.invalidate()
            return await self.request(method, path, tr_code, body, retry_on_401=False)

        if resp.status_code == 429:
            raise RateLimitError(f"API 호출 제한 초과: {path}")

        if resp.status_code >= 500:
            raise OrderError(f"서버 오류 {resp.status_code}: {path} - {resp.text[:200]}")

        if resp.status_code >= 400:
            raise OrderError(f"요청 오류 {resp.status_code}: {path} - {resp.text[:200]}")

        return resp.json()

    async def close(self):
        await self._http.aclose()
