"""
텔레그램 봇 단독 실행 스크립트

사용법:
    python scripts/run_telegram.py
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.types import AlertLevel
from app.bot.telegram_bot import TelegramBot
from app.monitoring.alerts import AlertManager
from app.monitoring.health import HealthCheck
from app.market.stock_pool import get_stock_pool, get_stock_name, get_pool_size


# ── 일봉 캐시 (당일 내 재사용) ──

class DailyBarCache:
    """당일 조회한 일봉 데이터를 캐시. 스캐너 반복 실행 시 API 재호출 방지."""

    def __init__(self):
        self._cache: dict[str, "pd.DataFrame"] = {}
        self._date: str = ""

    def _check_date(self):
        today = datetime.now().strftime("%Y%m%d")
        if self._date != today:
            self._cache.clear()
            self._date = today

    def get(self, code: str):
        self._check_date()
        return self._cache.get(code)

    def put(self, code: str, df):
        self._check_date()
        self._cache[code] = df

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def codes(self) -> set[str]:
        return set(self._cache.keys())


bar_cache = DailyBarCache()


# ── 스캐너 실행 ──

async def _fetch_one(md, code: str, today: str) -> bool:
    """종목 1개 일봉 조회 후 캐시 저장. 성공 시 True."""
    import pandas as pd
    try:
        resp = await md.get_daily_bars(code, base_dt=today)
        if resp.get("return_code") == 0:
            key = "stk_dt_pole_chart_qry"
            if key in resp and resp[key]:
                rows = []
                for r in resp[key]:
                    rows.append({
                        "datetime": pd.to_datetime(r["dt"]),
                        "open": float(r["open_pric"]),
                        "high": float(r["high_pric"]),
                        "low": float(r["low_pric"]),
                        "close": float(r["cur_prc"]),
                        "volume": int(r["trde_qty"]),
                        "stock_code": code,
                    })
                df = pd.DataFrame(rows).sort_values("datetime").reset_index(drop=True)
                bar_cache.put(code, df)
                return True
    except Exception:
        pass
    return False


async def run_scanner(scanner_name: str, progress_fn=None) -> str:
    from app.brokers.kiwoom.auth import KiwoomAuth
    from app.brokers.kiwoom.client import KiwoomClient
    from app.brokers.kiwoom.market_data import KiwoomMarketData
    from app.brokers.kiwoom.rate_limiter import RateLimiter
    from app.scanners.dsl import ScannerDSL
    from app.bot.keyboards import get_scanner_label
    import pandas as pd

    label = get_scanner_label(scanner_name)
    pool = get_stock_pool()
    codes = list(pool.keys())
    total = len(codes)

    # 캐시에 없는 종목만 API 호출
    uncached = [c for c in codes if bar_cache.get(c) is None]
    cached_count = total - len(uncached)

    if progress_fn:
        if cached_count > 0:
            await progress_fn(f"[{label}] {total}개 종목 중 {cached_count}개 캐시 사용, {len(uncached)}개 조회 시작")
        else:
            await progress_fn(f"[{label}] {total}개 종목 데이터 수집 시작...")

    if uncached:
        auth = KiwoomAuth(settings.kiwoom_app_key, settings.kiwoom_app_secret, settings.kiwoom_base_url)
        await auth.get_token()
        rl = RateLimiter(max_calls_per_second=2)  # 보수적 제한
        client = KiwoomClient(auth, rl, settings.kiwoom_base_url,
                              settings.kiwoom_app_key, settings.kiwoom_app_secret)
        md = KiwoomMarketData(client)

        today = datetime.now().strftime("%Y%m%d")
        failed: list[str] = []

        for i, code in enumerate(uncached, 1):
            name = get_stock_name(code)

            if progress_fn and (i == 1 or i % 20 == 0 or i == len(uncached)):
                await progress_fn(f"[{label}] {i}/{len(uncached)} 조회 중... ({name})")

            ok = await _fetch_one(md, code, today)
            if not ok:
                failed.append(code)
            await asyncio.sleep(0.4)

        # 실패 종목 재시도 (1회)
        if failed:
            if progress_fn:
                await progress_fn(f"[{label}] {len(failed)}개 종목 재시도 중...")
            await asyncio.sleep(2)  # 쿨다운
            for code in failed:
                await _fetch_one(md, code, today)
                await asyncio.sleep(0.5)

        await client.close()

    # 캐시에서 전체 데이터 조립
    bars = {}
    for code in codes:
        df = bar_cache.get(code)
        if df is not None:
            bars[code] = df

    if progress_fn:
        await progress_fn(f"[{label}] {len(bars)}개 종목 분석 중...")

    scanner = ScannerDSL.get_scanner(scanner_name)
    results = scanner.scan(bars)

    if not results:
        return f"[{label}] 완료\n{len(bars)}/{total}개 종목 스캔\n\n후보 종목 없음", []

    lines = [f"[{label}] 완료", f"{len(bars)}/{total}개 종목 스캔", ""]
    for i, r in enumerate(results, 1):
        name = get_stock_name(r.stock_code)
        reasons = ", ".join(r.reasons)
        lines.append(f"{i}. {r.stock_code} {name} ({r.score:.1f}점)")
        lines.append(f"   {reasons}")
    lines.append("\n종목명을 누르면 차트를 볼 수 있습니다.")
    return "\n".join(lines), results


# ── 차트 생성 ──

async def generate_chart(stock_code: str, scan_info: str = ""):
    """캐시된 일봉 데이터로 차트 이미지 생성"""
    from app.bot.chart import generate_chart

    df = bar_cache.get(stock_code)
    if df is None:
        return None

    return generate_chart(stock_code, df, scan_info)


# ── 메인 ──

async def main():
    if not settings.telegram_bot_token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set in .env")
        return
    if not settings.telegram_chat_id:
        print("[ERROR] TELEGRAM_CHAT_ID not set in .env")
        return

    print(f"=== Telegram Bot ===")
    print(f"Token: {settings.telegram_bot_token[:15]}...")
    print(f"Chat ID: {settings.telegram_chat_id}")
    print(f"Stock Pool: {get_pool_size()} stocks")
    print()

    # 전략 import (레지스트리 자동 등록)
    import app.strategies.momentum_breakout
    import app.strategies.pullback_trend
    import app.strategies.mean_reversion
    import app.strategies.low_volatility_trend
    import app.strategies.multi_factor

    bot = TelegramBot(settings.telegram_bot_token, settings.telegram_chat_id)

    # 헬스체크 연결
    health = HealthCheck()
    health.set_strategy("multi_factor")
    health.set_scheduler_running(False)
    bot.handlers.health_check = health

    # 스캐너 + 차트 콜백 연결
    bot.handlers.scanner_fn = run_scanner
    bot.handlers.chart_fn = generate_chart

    # 알림 매니저 연결
    async def send_alert(text: str):
        await bot.send_message(text)

    alert_mgr = AlertManager(send_fn=send_alert,
                             warning_enabled=settings.alert_level_warning,
                             info_enabled=settings.alert_level_info)
    bot.handlers.alert_manager = alert_mgr

    # 봇 시작
    await bot.start()
    print("[OK] Bot started. Commands registered.")
    print("[OK] Listening for messages... (Ctrl+C to stop)")

    # 시작 알림
    from app.bot.keyboards import MAIN_MENU_KEYBOARD
    await bot.send_message(
        f"Bot started.\nStock pool: {get_pool_size()} stocks\n/help 로 명령어를 확인하세요.",
        reply_markup=MAIN_MENU_KEYBOARD,
    )

    # 무한 대기
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        await bot.stop()
        print("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
