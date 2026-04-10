from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_no: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PositionRecord(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String)
    strategy_name: Mapped[str | None] = mapped_column(String)
    qty: Mapped[int] = mapped_column(Integer, default=0)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0)
    current_price: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    entry_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (Index("idx_positions_account", "account_id"),)


class OrderRecord(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String)
    strategy_name: Mapped[str | None] = mapped_column(String)
    side: Mapped[str] = mapped_column(String, nullable=False)
    order_type: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="pending")
    broker_order_no: Mapped[str | None] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index("idx_orders_account_status", "account_id", "status"),
        Index("idx_orders_stock_code", "stock_code"),
    )


class FillRecord(Base):
    __tablename__ = "fills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    slippage: Mapped[float | None] = mapped_column(Float)
    commission: Mapped[float | None] = mapped_column(Float)
    tax: Mapped[float | None] = mapped_column(Float)
    fill_time_ms: Mapped[int | None] = mapped_column(Integer)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime)

    __table_args__ = (Index("idx_fills_order", "order_id"),)


class DailyBar(Base):
    __tablename__ = "daily_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)
    turnover: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("stock_code", "date"),
        Index("idx_daily_bars_code_date", "stock_code", "date"),
    )


class MinuteBar(Base):
    __tablename__ = "minute_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval: Mapped[int] = mapped_column(Integer, default=1)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)
    turnover: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("stock_code", "datetime", "interval"),
        Index("idx_minute_bars_code_dt", "stock_code", "datetime"),
    )


class ResampledBar(Base):
    __tablename__ = "resampled_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interval: Mapped[int] = mapped_column(Integer, nullable=False)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("stock_code", "datetime", "interval"),)


class SignalRecord(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str | None] = mapped_column(String)
    score: Mapped[float | None] = mapped_column(Float)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (Index("idx_signals_strategy_time", "strategy_name", "created_at"),)


class StrategyRun(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="running")
    params_json: Mapped[str | None] = mapped_column(Text)


class StrategySelection(Base):
    __tablename__ = "strategy_selections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    selected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    selected_by: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("idx_strategy_selections_time", "selected_at"),)


class ScannerRule(Base):
    __tablename__ = "scanner_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    config_yaml: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class ScannerRun(Base):
    __tablename__ = "scanner_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scanner_name: Mapped[str] = mapped_column(String, nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    result_count: Mapped[int] = mapped_column(Integer, default=0)


class ScannerResult(Base):
    __tablename__ = "scanner_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    stock_name: Mapped[str | None] = mapped_column(String)
    score: Mapped[float | None] = mapped_column(Float)
    reasons: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("idx_scanner_results_run", "run_id"),)


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    command: Mapped[str | None] = mapped_column(String)
    message: Mapped[str | None] = mapped_column(Text)
    alert_level: Mapped[str | None] = mapped_column(String)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_type: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    strategy_names: Mapped[str | None] = mapped_column(Text)
    strategy_changes_json: Mapped[str | None] = mapped_column(Text)
    realized_pnl: Mapped[float | None] = mapped_column(Float)
    unrealized_pnl: Mapped[float | None] = mapped_column(Float)
    total_return_pct: Mapped[float | None] = mapped_column(Float)
    mdd_pct: Mapped[float | None] = mapped_column(Float)
    total_trades: Mapped[int | None] = mapped_column(Integer)
    win_rate: Mapped[float | None] = mapped_column(Float)
    avg_profit_loss_ratio: Mapped[float | None] = mapped_column(Float)
    benchmark_return_pct: Mapped[float | None] = mapped_column(Float)
    excess_return_pct: Mapped[float | None] = mapped_column(Float)
    report_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("idx_performance_reviews_type_period", "review_type", "period_start"),
    )


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_names: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_cash: Mapped[float | None] = mapped_column(Float)
    timeframe: Mapped[str | None] = mapped_column(String)
    params_json: Mapped[str | None] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    strategy_name: Mapped[str | None] = mapped_column(String)
    stock_code: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    entry_time: Mapped[datetime | None] = mapped_column(DateTime)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime)
    entry_price: Mapped[float | None] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float)
    qty: Mapped[int | None] = mapped_column(Integer)
    pnl: Mapped[float | None] = mapped_column(Float)
    mfe: Mapped[float | None] = mapped_column(Float)
    mae: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (Index("idx_backtest_trades_run", "run_id"),)


class BacktestEquityCurve(Base):
    __tablename__ = "backtest_equity_curve"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    daily_return_pct: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (Index("idx_backtest_equity_run", "run_id"),)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    report_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TradingCalendar(Base):
    __tablename__ = "trading_calendar"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    is_trading_day: Mapped[bool] = mapped_column(Boolean, default=True)
    is_half_day: Mapped[bool] = mapped_column(Boolean, default=False)
    close_time: Mapped[str | None] = mapped_column(String)
    note: Mapped[str | None] = mapped_column(Text)


class StrategyParamProfile(Base):
    __tablename__ = "strategy_param_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String, nullable=False)
    profile_name: Mapped[str] = mapped_column(String, nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("strategy_name", "profile_name"),)


class SlippageStat(Base):
    __tablename__ = "slippage_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    stock_code: Mapped[str | None] = mapped_column(String)
    avg_slippage_pct: Mapped[float | None] = mapped_column(Float)
    max_slippage_pct: Mapped[float | None] = mapped_column(Float)
    unfilled_rate: Mapped[float | None] = mapped_column(Float)
    avg_fill_time_ms: Mapped[float | None] = mapped_column(Float)
    sample_count: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("date", "stock_code"),
        Index("idx_slippage_date", "date"),
    )
