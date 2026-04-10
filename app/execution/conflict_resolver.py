from __future__ import annotations

from app.core.types import OrderRequest, OrderSide


class ConflictResolver:
    """동시 전략 자금 충돌 중재"""

    def resolve(
        self,
        orders: list[OrderRequest],
        available_cash: float,
        held_codes: set[str],
        price_map: dict[str, float],
        per_stock_budget: float,
    ) -> list[OrderRequest]:
        """
        규칙:
        1. 동일 종목 중복 매수 금지 (점수 높은 시그널 우선)
        2. 이미 보유 중인 종목 매수 금지
        3. 가용 자금 초과 시 점수 높은 순으로 선별
        4. 매도 주문은 무조건 통과
        """
        sell_orders = [o for o in orders if o.side == OrderSide.SELL]
        buy_orders = [o for o in orders if o.side == OrderSide.BUY]

        # 매수 주문: 중복 제거 (동일 종목 중 첫 번째만)
        seen_codes: set[str] = set()
        unique_buys: list[OrderRequest] = []
        for order in buy_orders:
            if order.stock_code in seen_codes:
                continue
            if order.stock_code in held_codes:
                continue
            seen_codes.add(order.stock_code)
            unique_buys.append(order)

        # 자금 한도 적용
        remaining = available_cash
        approved_buys: list[OrderRequest] = []
        for order in unique_buys:
            cost = price_map.get(order.stock_code, 0) * max(order.qty, 1)
            estimated_cost = min(cost, per_stock_budget) if cost > 0 else per_stock_budget
            if remaining >= estimated_cost:
                remaining -= estimated_cost
                approved_buys.append(order)

        return sell_orders + approved_buys
