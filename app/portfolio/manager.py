from __future__ import annotations

from app.core.types import AccountState, Position


class PortfolioManager:
    """포지션 관리 및 평가"""

    def __init__(self):
        self._positions: dict[str, Position] = {}

    @property
    def positions(self) -> list[Position]:
        return list(self._positions.values())

    @property
    def count(self) -> int:
        return len(self._positions)

    def get(self, stock_code: str) -> Position | None:
        return self._positions.get(stock_code)

    def add_or_update(self, position: Position):
        if position.qty <= 0:
            self._positions.pop(position.stock_code, None)
        else:
            self._positions[position.stock_code] = position

    def remove(self, stock_code: str):
        self._positions.pop(stock_code, None)

    def update_price(self, stock_code: str, price: float):
        pos = self._positions.get(stock_code)
        if pos:
            pos.current_price = price

    def total_equity(self, cash: float) -> float:
        market_value = sum(p.current_price * p.qty for p in self._positions.values())
        return cash + market_value

    def total_unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self._positions.values())

    def sync_from_list(self, positions: list[Position]):
        self._positions = {p.stock_code: p for p in positions if p.qty > 0}
