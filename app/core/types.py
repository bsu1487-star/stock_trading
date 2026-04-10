from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    BEST = "best"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalAction(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    HOLD = "hold"


class AlertLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class MarketPhase(str, Enum):
    PRE_MARKET = "pre_market"
    OPENING = "opening"
    REGULAR = "regular"
    CLOSING = "closing"
    POST_MARKET = "post_market"
    CLOSED = "closed"


@dataclass
class Signal:
    stock_code: str
    action: SignalAction
    side: OrderSide | None = None
    reason: str = ""
    score: float = 0.0
    target_price: float | None = None
    stop_price: float | None = None
    strategy_name: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrderRequest:
    stock_code: str
    stock_name: str
    side: OrderSide
    order_type: OrderType
    qty: int
    price: float = 0.0
    strategy_name: str = ""
    reason: str = ""


@dataclass
class Position:
    stock_code: str
    stock_name: str
    strategy_name: str
    qty: int
    avg_price: float
    current_price: float = 0.0
    entry_at: datetime | None = None

    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.avg_price) * self.qty

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_price == 0:
            return 0.0
        return (self.current_price - self.avg_price) / self.avg_price * 100


@dataclass
class AccountState:
    total_equity: float = 0.0
    available_cash: float = 0.0
    positions: list[Position] = field(default_factory=list)
    daily_realized_pnl: float = 0.0
    daily_loss_count: int = 0
    consecutive_losses: int = 0
