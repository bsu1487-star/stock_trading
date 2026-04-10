"""
스캐너 실행 스크립트

사용법:
    python scripts/run_scanner.py
    python scripts/run_scanner.py --scanner volume_breakout
    python scripts/run_scanner.py --scanner c_spot --top 10
    python scripts/run_scanner.py --list
"""

import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.brokers.kiwoom.auth import KiwoomAuth
from app.brokers.kiwoom.client import KiwoomClient
from app.brokers.kiwoom.market_data import KiwoomMarketData
from app.brokers.kiwoom.rate_limiter import RateLimiter
from app.scanners.dsl import ScannerDSL
from app.market.stock_pool import get_stock_codes, get_stock_name, get_pool_size

import pandas as pd
from datetime import datetime


async def fetch_bars(md: KiwoomMarketData, codes: list[str]) -> dict[str, pd.DataFrame]:
    bars = {}
    today = datetime.now().strftime("%Y%m%d")
    total = len(codes)
    for i, code in enumerate(codes, 1):
        name = get_stock_name(code)
        if i == 1 or i % 20 == 0 or i == total:
            print(f"  {i}/{total} {code} {name}...")
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
                    bars[code] = pd.DataFrame(rows).sort_values("datetime").reset_index(drop=True)
        except Exception:
            pass
        await asyncio.sleep(0.25)
    return bars


async def main():
    parser = argparse.ArgumentParser(description="scanner runner")
    parser.add_argument("--scanner", default="volume_breakout", help="scanner name")
    parser.add_argument("--top", type=int, default=10, help="show top N results")
    parser.add_argument("--list", action="store_true", help="list available scanners")
    parser.add_argument("--stocks", nargs="+", default=None, help="stock codes (default: full pool)")
    args = parser.parse_args()

    if args.list:
        print("Available scanners:")
        for name in ScannerDSL.list_scanners():
            print(f"  - {name}")
        print(f"\nStock pool: {get_pool_size()} stocks")
        return

    codes = args.stocks or get_stock_codes()
    print(f"\n=== Scanner: {args.scanner} ===")
    print(f"Scanning {len(codes)} stocks...")

    # 데이터 수집
    auth = KiwoomAuth(settings.kiwoom_app_key, settings.kiwoom_app_secret, settings.kiwoom_base_url)
    await auth.get_token()
    rl = RateLimiter(max_calls_per_second=3)
    client = KiwoomClient(auth, rl, settings.kiwoom_base_url,
                          settings.kiwoom_app_key, settings.kiwoom_app_secret)
    md = KiwoomMarketData(client)

    bars = await fetch_bars(md, codes)
    await client.close()

    print(f"Fetched {len(bars)} stocks.\n")

    # 스캐너 실행
    scanner = ScannerDSL.get_scanner(args.scanner)
    results = scanner.scan(bars)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} candidates (top {args.top}):\n")
    print(f"{'Rank':<5} {'Code':<8} {'Name':<12} {'Score':<8} {'Reasons'}")
    print("-" * 75)
    for i, r in enumerate(results[:args.top], 1):
        name = get_stock_name(r.stock_code)
        reasons = ", ".join(r.reasons)
        print(f"{i:<5} {r.stock_code:<8} {name:<12} {r.score:<8.1f} {reasons}")


if __name__ == "__main__":
    asyncio.run(main())
