"""슬리피지/수수료/세금 모델"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostModel:
    slippage_pct: float = 0.10        # 슬리피지 (%)
    commission_pct: float = 0.015     # 수수료 (%)
    tax_pct: float = 0.20             # 거래세 (%, 매도 시만)

    def apply_buy(self, price: float, qty: int) -> tuple[float, float]:
        """매수 체결가 및 수수료 계산"""
        fill_price = price * (1 + self.slippage_pct / 100)
        commission = fill_price * qty * (self.commission_pct / 100)
        return fill_price, commission

    def apply_sell(self, price: float, qty: int) -> tuple[float, float, float]:
        """매도 체결가, 수수료, 세금 계산"""
        fill_price = price * (1 - self.slippage_pct / 100)
        commission = fill_price * qty * (self.commission_pct / 100)
        tax = fill_price * qty * (self.tax_pct / 100)
        return fill_price, commission, tax
