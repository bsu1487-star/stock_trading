from __future__ import annotations

from app.core.constants import PATH_CHART, TR_CHART_DAILY, TR_CHART_MINUTE

from .client import KiwoomClient


class KiwoomMarketData:
    """차트/시세 조회"""

    def __init__(self, client: KiwoomClient):
        self._client = client

    async def get_daily_bars(self, stock_code: str, base_dt: str = "", count: int = 100) -> dict:
        """일봉 차트 조회 (ka10081)"""
        body = {
            "stk_cd": stock_code,
            "upd_stkpc_tp": "1",
        }
        if base_dt:
            body["base_dt"] = base_dt
        return await self._client.request("POST", PATH_CHART, TR_CHART_DAILY, body)

    async def get_minute_bars(
        self,
        stock_code: str,
        interval: int = 1,
        count: int = 500,
    ) -> dict:
        """분봉 차트 조회 (ka10080)"""
        return await self._client.request(
            "POST",
            PATH_CHART,
            TR_CHART_MINUTE,
            {
                "stk_cd": stock_code,
                "tic_scope": str(interval),
                "upd_stkpc_tp": "1",
            },
        )
