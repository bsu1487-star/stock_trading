from __future__ import annotations

import math


class PositionSizer:
    """포지션 sizing"""

    @staticmethod
    def equal_weight(available_cash: float, max_positions: int, price: float) -> int:
        """동일가중: 가용자금 / 최대종목수 / 현재가"""
        if price <= 0 or max_positions <= 0:
            return 0
        budget = available_cash / max_positions
        return math.floor(budget / price)

    @staticmethod
    def volatility_inverse(available_cash: float, atr: float, price: float, risk_per_trade: float = 0.01) -> int:
        """변동성 역가중: 위험금액 / ATR"""
        if atr <= 0 or price <= 0:
            return 0
        risk_amount = available_cash * risk_per_trade
        qty = math.floor(risk_amount / atr)
        max_qty = math.floor(available_cash * 0.2 / price)  # 1종목 최대 20%
        return min(qty, max_qty)

    @staticmethod
    def fixed_amount(amount: float, price: float) -> int:
        """고정 금액"""
        if price <= 0:
            return 0
        return math.floor(amount / price)
