from __future__ import annotations

from app.core.constants import PATH_ACCOUNT, TR_BALANCE, TR_DEPOSIT, TR_PENDING

from .client import KiwoomClient


class KiwoomAccount:
    """계좌/예수금/잔고/미체결 조회"""

    def __init__(self, client: KiwoomClient, account_no: str):
        self._client = client
        self._account_no = account_no

    async def get_deposit(self) -> dict:
        """예수금상세현황 조회 (ka10170)"""
        return await self._client.request(
            "POST",
            PATH_ACCOUNT,
            TR_DEPOSIT,
            {
                "acnt_no": self._account_no,
                "ottks_tp": "01",
                "ch_crd_tp": "01",
            },
        )

    async def get_balance(self) -> dict:
        """계좌별당일현황 조회 (kt00017)"""
        return await self._client.request(
            "POST",
            PATH_ACCOUNT,
            TR_BALANCE,
            {
                "acnt_no": self._account_no,
            },
        )

    async def get_pending_orders(self) -> dict:
        """미체결 조회 (ka10075)"""
        return await self._client.request(
            "POST",
            PATH_ACCOUNT,
            TR_PENDING,
            {
                "acnt_no": self._account_no,
                "all_stk_tp": "0",
                "sll_buy_tp": "0",
                "sort_tp": "1",
                "trde_tp": "0",
                "stex_tp": "0",
            },
        )
