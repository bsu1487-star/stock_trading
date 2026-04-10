"""텔레그램 메시지 포맷터"""

from __future__ import annotations

from app.core.types import AccountState, Position


def format_status(account_state: AccountState, strategy_name: str, bot_running: bool) -> str:
    status = "실행 중" if bot_running else "정지"
    lines = [
        f"[상태 요약]",
        f"봇: {status}",
        f"전략: {strategy_name}",
        f"총 평가금: {account_state.total_equity:,.0f}원",
        f"가용 현금: {account_state.available_cash:,.0f}원",
        f"당일 실현손익: {account_state.daily_realized_pnl:+,.0f}원",
        f"보유 종목: {len(account_state.positions)}개",
    ]
    return "\n".join(lines)


def format_positions(positions: list[Position]) -> str:
    if not positions:
        return "보유 종목이 없습니다."
    lines = ["[보유 종목]"]
    for p in positions:
        lines.append(
            f"  {p.stock_code} {p.stock_name} | "
            f"{p.qty}주 | 평균가 {p.avg_price:,.0f} | "
            f"현재가 {p.current_price:,.0f} | "
            f"수익률 {p.unrealized_pnl_pct:+.1f}%"
        )
    return "\n".join(lines)


def format_order_alert(
    side: str, strategy: str, stock_code: str, stock_name: str,
    qty: int, price: float, reason: str,
) -> str:
    label = "매수 체결" if side == "buy" else "매도 체결"
    return (
        f"[{label}]\n"
        f"전략: {strategy}\n"
        f"종목: {stock_code} {stock_name}\n"
        f"수량: {qty}\n"
        f"체결가: {price:,.0f}\n"
        f"사유: {reason}"
    )


def format_daily_review(
    date_str: str,
    strategy: str,
    realized_pnl: float,
    unrealized_pnl: float,
    total_return_pct: float,
    trades: int,
    win_rate: float,
    benchmark_return_pct: float | None = None,
) -> str:
    lines = [
        f"[일간 성과리뷰]",
        f"기준일: {date_str}",
        f"활성 전략: {strategy}",
        f"실현손익: {realized_pnl:+,.0f}원",
        f"평가손익: {unrealized_pnl:+,.0f}원",
        f"총수익률: {total_return_pct:+.2f}%",
        f"매매횟수: {trades}",
        f"승률: {win_rate:.0f}%",
    ]
    if benchmark_return_pct is not None:
        excess = total_return_pct - benchmark_return_pct
        lines.append(f"KOSPI 대비: {excess:+.2f}%")
    return "\n".join(lines)
