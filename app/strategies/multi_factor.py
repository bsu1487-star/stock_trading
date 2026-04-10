"""전략 5. 멀티팩터 랭킹 전략 (메인 전략)"""

from __future__ import annotations

import pandas as pd

from app.core.types import AccountState, OrderRequest, OrderSide, OrderType, Signal, SignalAction
from app.market.indicators import TechnicalIndicators as TI

from .base import Strategy
from .registry import StrategyRegistry


@StrategyRegistry.register
class MultiFactor(Strategy):
    name = "multi_factor"
    timeframe = "5m"
    warmup_bars = 60
    max_positions = 5
    supports_overnight = True

    def __init__(self, top_n: int = 5, stop_loss_pct: float = 3.0, rebalance_threshold: float = 20.0):
        self.top_n = top_n
        self.stop_loss_pct = stop_loss_pct
        self.rebalance_threshold = rebalance_threshold

    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        bars = bars.copy()
        bars["return_20"] = bars["close"].pct_change(20) * 100
        bars["return_60"] = bars["close"].pct_change(60) * 100
        bars["vol_ratio"] = TI.volume_ratio(bars["volume"], 20)
        bars["sma_20"] = TI.sma(bars["close"], 20)
        bars["sma_60"] = TI.sma(bars["close"], 60)
        bars["atr_20"] = TI.atr(bars, 20)
        bars["rsi_14"] = TI.rsi(bars["close"], 14)
        return bars

    def score_stock(self, row: pd.Series) -> float:
        """팩터 점수 계산"""
        score = 0.0

        # 20일 수익률 점수 (모멘텀)
        r20 = row.get("return_20", 0)
        if r20 > 0:
            score += min(r20, 30)  # 최대 30점

        # 60일 수익률 점수 (중기 모멘텀)
        r60 = row.get("return_60", 0)
        if r60 > 0:
            score += min(r60 * 0.5, 15)  # 최대 15점

        # 거래대금 점수
        vr = row.get("vol_ratio", 0)
        if vr > 1.0:
            score += min(vr * 5, 20)  # 최대 20점

        # 추세 정배열 점수
        sma20 = row.get("sma_20", 0)
        sma60 = row.get("sma_60", 0)
        if sma20 > sma60 > 0:
            score += 15

        # 과도한 갭 상승 패널티
        if r20 > 30:
            score -= 10

        # 변동성 패널티
        atr = row.get("atr_20", 0)
        close = row.get("close", 1)
        if close > 0 and atr / close > 0.03:
            score -= 10

        return max(score, 0)

    def on_bar(self, current_time, data_slice: pd.DataFrame, positions: list, account_state: AccountState) -> list[Signal]:
        if len(data_slice) < self.warmup_bars:
            return []

        signals = []
        last = data_slice.iloc[-1]
        stock_code = last.get("stock_code", "")

        # 개별 종목 평가 시그널 생성
        if stock_code:
            score = self.score_stock(last)
            if score > self.rebalance_threshold:
                held_codes = {p.stock_code for p in positions}
                if stock_code not in held_codes:
                    signals.append(
                        Signal(
                            stock_code=stock_code,
                            action=SignalAction.ENTRY,
                            side=OrderSide.BUY,
                            reason=f"멀티팩터 상위 (점수={score:.1f})",
                            score=score,
                            strategy_name=self.name,
                        )
                    )

        # 손절
        for pos in positions:
            if pos.strategy_name != self.name:
                continue
            if pos.unrealized_pnl_pct <= -self.stop_loss_pct:
                signals.append(
                    Signal(stock_code=pos.stock_code, action=SignalAction.EXIT, side=OrderSide.SELL,
                           reason=f"손절 {pos.unrealized_pnl_pct:.1f}%", strategy_name=self.name))

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
