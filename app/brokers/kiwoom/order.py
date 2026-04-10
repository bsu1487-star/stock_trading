from __future__ import annotations

from app.core.constants import PATH_ORDER, TR_BUY, TR_CANCEL, TR_MODIFY, TR_SELL

from .client import KiwoomClient


class KiwoomOrder:
    """주문/정정/취소"""

    def __init__(self, client: KiwoomClient, account_no: str):
        self._client = client
        self._account_no = account_no

    async def buy(
        self,
        stock_code: str,
        qty: int,
        price: int = 0,
        order_type: str = "00",
    ) -> dict:
        """매수 주문 (kt10000). order_type: 00=지정가, 03=시장가, 05=최유리"""
        return await self._client.request(
            "POST",
            PATH_ORDER,
            TR_BUY,
            {
                "acnt_no": self._account_no,
                "stk_cd": stock_code,
                "ord_qty": str(qty),
                "ord_prc": str(price),
                "ord_tp": order_type,
            },
        )

    async def sell(
        self,
        stock_code: str,
        qty: int,
        price: int = 0,
        order_type: str = "00",
    ) -> dict:
        """매도 주문 (kt10001)"""
        return await self._client.request(
            "POST",
            PATH_ORDER,
            TR_SELL,
            {
                "acnt_no": self._account_no,
                "stk_cd": stock_code,
                "ord_qty": str(qty),
                "ord_prc": str(price),
                "ord_tp": order_type,
            },
        )

    async def modify(
        self,
        org_order_no: str,
        qty: int,
        price: int,
    ) -> dict:
        """정정 주문 (kt10002)"""
        return await self._client.request(
            "POST",
            PATH_ORDER,
            TR_MODIFY,
            {
                "acnt_no": self._account_no,
                "org_ord_no": org_order_no,
                "ord_qty": str(qty),
                "ord_prc": str(price),
            },
        )

    async def cancel(self, org_order_no: str, qty: int) -> dict:
        """취소 주문 (kt10003)"""
        return await self._client.request(
            "POST",
            PATH_ORDER,
            TR_CANCEL,
            {
                "acnt_no": self._account_no,
                "org_ord_no": org_order_no,
                "ord_qty": str(qty),
            },
        )
