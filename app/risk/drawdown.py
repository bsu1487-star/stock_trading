from __future__ import annotations


class DrawdownManager:
    """드로다운 기반 동적 포지션 축소"""

    def __init__(self, reduce_threshold_pct: float = 1.0, stop_threshold_pct: float = 2.0):
        self.reduce_threshold_pct = reduce_threshold_pct
        self.stop_threshold_pct = stop_threshold_pct
        self._peak_equity: float = 0.0

    def update_peak(self, equity: float):
        if equity > self._peak_equity:
            self._peak_equity = equity

    @property
    def peak_equity(self) -> float:
        return self._peak_equity

    def current_mdd_pct(self, equity: float) -> float:
        if self._peak_equity <= 0:
            return 0.0
        return (self._peak_equity - equity) / self._peak_equity * 100

    def get_weight_multiplier(self, equity: float) -> float:
        """
        MDD 기반 비중 조절:
        - MDD < reduce_threshold: 1.0 (정상)
        - reduce_threshold <= MDD < stop_threshold: 0.5 (비중 50% 축소)
        - MDD >= stop_threshold: 0.0 (신규 진입 중지)
        """
        mdd = self.current_mdd_pct(equity)
        if mdd >= self.stop_threshold_pct:
            return 0.0
        if mdd >= self.reduce_threshold_pct:
            return 0.5
        return 1.0
