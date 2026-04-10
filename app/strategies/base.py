from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from app.core.types import AccountState, OrderRequest, Signal


class Strategy(ABC):
    """전략 공통 인터페이스. on_bar() 기반 구조."""

    name: str = ""
    timeframe: str = "5m"
    warmup_bars: int = 60
    max_positions: int = 5
    supports_overnight: bool = False

    @abstractmethod
    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        """지표 계산 및 피처 생성. 원본 DataFrame에 컬럼 추가 후 반환."""
        ...

    @abstractmethod
    def on_bar(
        self,
        current_time,
        data_slice: pd.DataFrame,
        positions: list,
        account_state: AccountState,
    ) -> list[Signal]:
        """새로운 봉 도착 시 호출. 시그널 리스트 반환."""
        ...

    @abstractmethod
    def generate_orders(
        self,
        signals: list[Signal],
        positions: list,
        account_state: AccountState,
    ) -> list[OrderRequest]:
        """시그널 기반으로 실제 주문 생성."""
        ...
