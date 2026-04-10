"""전략 4. 저변동성 추세 지속 전략"""

from __future__ import annotations

import pandas as pd

from app.core.types import AccountState, OrderRequest, OrderSide, OrderType, Signal, SignalAction
from app.market.indicators import TechnicalIndicators as TI

from .base import Strategy
from .registry import StrategyRegistry


@StrategyRegistry.register
class LowVolTrend(Strategy):
    name = "low_volatility_trend"
    timeframe = "15m"
    warmup_bars = 80
    max_positions = 5
    supports_overnight = True

    def __init__(self, vol_percentile: float = 50.0, stop_loss_pct: float = 3.0):
        self.vol_percentile = vol_percentile
        self.stop_loss_pct = stop_loss_pct

    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        bars = bars.copy()
        bars["sma_20"] = TI.sma(bars["close"], 20)
        bars["sma_60"] = TI.sma(bars["close"], 60)
        bars["atr_20"] = TI.atr(bars, 20)
        bars["return_60"] = bars["close"].pct_change(60) * 100
        bars["ma_slope_20"] = TI.ma_slope(bars["close"], 20, 5)
        return bars

    def on_bar(self, current_time, data_slice: pd.DataFrame, positions: list, account_state: AccountState) -> list[Signal]:
        if len(data_slice) < self.warmup_bars:
            return []

        signals = []
        last = data_slice.iloc[-1]
        held_codes = {p.stock_code for p in positions}
        stock_code = last.get("stock_code", "")

        if stock_code and stock_code not in held_codes:
            # 60일 수익률 양수
            positive_return = last["return_60"] > 0
            # 이평선 우상향
            trend_up = last["sma_20"] > last["sma_60"]
            slope_up = last["ma_slope_20"] > 0
            # 변동성이 낮음 (ATR 기준)
            atr_series = data_slice["atr_20"].dropna()
            if len(atr_series) > 0:
                low_vol = last["atr_20"] < atr_series.quantile(self.vol_percentile / 100)
            else:
                low_vol = False

            if positive_return and trend_up and slope_up and low_vol:
                signals.append(
                    Signal(
                        stock_code=stock_code,
                        action=SignalAction.ENTRY,
                        side=OrderSide.BUY,
                        reason=f"저변동성 추세: 60일수익={last['return_60']:.1f}%, 이평 정배열",
                        score=last["return_60"],
                        strategy_name=self.name,
                    )
                )

        for pos in positions:
            if pos.strategy_name != self.name:
                continue
            if pos.unrealized_pnl_pct <= -self.stop_loss_pct:
                signals.append(Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                                      reason=f"손절 {pos.unrealized_pnl_pct:.1f}%", strategy_name=self.name))
            elif last.get("close", 0) < last.get("sma_20", 0):
                signals.append(Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                                      reason="20일선 이탈", strategy_name=self.name))

        return signals

    def generate_orders(self, signals: list[Signal], positions: list, account_state: AccountState) -> list[OrderRequest]:
        orders = []
        for sig in signals:
            if sig.action == SignalAction.ENTRY:
                orders.append(OrderRequest(stock_code=sig.stock_code, stock_name="", side=OrderSide.BUY,
                                           order_type=OrderType.MARKET, qty=0, strategy_name=self.name, reason=sig.reason))
            elif sig.action == SignalAction.EXIT:
                pos = next((p for p in positions if p.stock_code == sig.stock_code), None)
                if pos:
                    orders.append(OrderRequest(stock_code=sig.stock_code, stock_name=pos.stock_name, side=OrderSide.SELL,
                                               order_type=OrderType.MARKET, qty=pos.qty, strategy_name=self.name, reason=sig.reason))
        return orders
