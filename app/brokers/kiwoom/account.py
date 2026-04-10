from __future__ import annotations

from app.core.constants import PATH_ACCOUNT, TR_BALANCE, TR_DEPOSIT, TR_PENDING

from .client import KiwoomClient


class KiwoomAccount:
    """계좌/예수금/잔고/미체결 조회"""

    def __init__(self, client: KiwoomClient, account_no: str):
        self._client = client
        self._account_no = account_no

    async def get_deposit(self) -> dict:
        """예수금 조회 (ka10170)"""
        return await self._client.request(
            "POST",
            PATH_ACCOUNT,
            TR_DEPOSIT,
            {"acnt_no": self._account_no},
        )

    async def get_balance(self) -> dict:
        """계좌평가잔고 조회 (kt00017)"""
        return await self._client.request(
            "POST",
            PATH_ACCOUNT,
            TR_BALANCE,
            {"acnt_no": self._account_no},
        )

    async def get_pending_orders(self) -> dict:
        """미체결 조회 (ka10075)"""
        return await self._client.request(
            "POST",
            PATH_ACCOUNT,
            TR_PENDING,
            {"acnt_no": self._account_no},
        )
