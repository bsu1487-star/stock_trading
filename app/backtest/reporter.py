"""백테스트 결과 리포트"""

from __future__ import annotations

from app.backtest.engine import BacktestResult


class BacktestReporter:
    """백테스트 결과를 리포트 형태로 생성"""

    @staticmethod
    def generate(result: BacktestResult, strategy_name: str = "") -> dict:
        return {
            "strategy": strategy_name,
            "initial_cash": result.initial_cash,
            "final_equity": round(result.final_equity, 0),
            "total_return_pct": round(result.total_return_pct, 2),
            "total_trades": result.total_trades,
            "win_rate": round(result.win_rate, 1),
            "profit_factor": round(result.profit_factor, 2),
            "mdd_pct": round(result.mdd_pct, 2),
        }

    @staticmethod
    def to_text(report: dict) -> str:
        lines = [
            "=== 백테스트 결과 ===",
            f"전략: {report.get('strategy', '')}",
            f"초기 자금: {report['initial_cash']:,.0f}원",
            f"최종 자산: {report['final_equity']:,.0f}원",
            f"총 수익률: {report['total_return_pct']:+.2f}%",
            f"총 거래 수: {report['total_trades']}",
            f"승률: {report['win_rate']:.1f}%",
            f"Profit Factor: {report['profit_factor']:.2f}",
            f"MDD: {report['mdd_pct']:.2f}%",
        ]
        return "\n".join(lines)
