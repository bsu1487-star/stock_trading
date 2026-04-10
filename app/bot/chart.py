"""스캔 결과 종목 차트 생성"""

from __future__ import annotations

import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # GUI 없는 환경
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np

# 한글 폰트 설정 (Windows: Malgun Gothic)
for font_name in ["Malgun Gothic", "NanumGothic", "AppleGothic"]:
    if any(font_name in f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = font_name
        break
plt.rcParams["axes.unicode_minus"] = False

from app.market.indicators import TechnicalIndicators as TI
from app.market.stock_pool import get_stock_name


def generate_chart(code: str, df: pd.DataFrame, scan_info: str = "") -> io.BytesIO:
    """
    종목 차트 이미지를 BytesIO로 반환.

    차트 구성:
    - 상단: 캔들(종가 라인) + 이동평균선 (5/20/60일)
    - 하단: 거래량 바
    """
    name = get_stock_name(code)
    df = df.copy().tail(60)  # 최근 60일

    if "datetime" in df.columns:
        df["date"] = pd.to_datetime(df["datetime"])
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    else:
        df["date"] = range(len(df))

    # 이동평균 계산 (원본 전체에서 계산 후 tail)
    close = df["close"].astype(float)
    df["ma5"] = TI.sma(close, 5)
    df["ma20"] = TI.sma(close, 20)
    df["ma60"] = TI.sma(close, 60)

    # 색상
    up_color = "#FF4444"
    down_color = "#4488FF"
    colors = [up_color if c >= o else down_color for c, o in zip(df["close"], df["open"])]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6), height_ratios=[3, 1],
        gridspec_kw={"hspace": 0.05},
    )

    dates = df["date"]
    x = range(len(df))

    # ── 상단: 가격 + 이평선 ──

    # 캔들 바디
    for i, (idx, row) in enumerate(df.iterrows()):
        o, c = float(row["open"]), float(row["close"])
        h, l = float(row["high"]), float(row["low"])
        color = up_color if c >= o else down_color

        # 꼬리
        ax1.plot([i, i], [l, h], color=color, linewidth=0.8)
        # 몸통
        body_bottom = min(o, c)
        body_height = abs(c - o)
        if body_height == 0:
            body_height = h * 0.001
        ax1.bar(i, body_height, bottom=body_bottom, width=0.6, color=color, edgecolor=color)

    # 이동평균선
    ax1.plot(x, df["ma5"], color="#FFB300", linewidth=1.2, label="MA5", alpha=0.9)
    ax1.plot(x, df["ma20"], color="#FF5722", linewidth=1.2, label="MA20", alpha=0.9)
    if df["ma60"].notna().any():
        ax1.plot(x, df["ma60"], color="#2196F3", linewidth=1.2, label="MA60", alpha=0.9)

    # 현재가 수평선
    last_close = float(df["close"].iloc[-1])
    ax1.axhline(y=last_close, color="#888888", linewidth=0.5, linestyle="--", alpha=0.5)
    ax1.text(len(df) - 1, last_close, f" {last_close:,.0f}", fontsize=8, color="#888888", va="bottom")

    # 타이틀
    pct_change = (float(df["close"].iloc[-1]) - float(df["close"].iloc[0])) / float(df["close"].iloc[0]) * 100
    title = f"{code} {name}  |  {last_close:,.0f}원  ({pct_change:+.1f}%)"
    if scan_info:
        title += f"\n{scan_info}"
    ax1.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=10)

    ax1.legend(loc="upper left", fontsize=8, framealpha=0.7)
    ax1.set_xlim(-1, len(df))
    ax1.set_xticks([])
    ax1.grid(True, alpha=0.2)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{v:,.0f}"))

    # ── 하단: 거래량 ──

    vol = df["volume"].astype(float)
    vol_colors = [up_color if c >= o else down_color for c, o in zip(df["close"], df["open"])]
    ax2.bar(x, vol, width=0.6, color=vol_colors, alpha=0.6)

    # 거래량 20일 평균선
    vol_ma = TI.sma(vol, 20)
    ax2.plot(x, vol_ma, color="#FF9800", linewidth=1, alpha=0.8)

    ax2.set_xlim(-1, len(df))
    ax2.grid(True, alpha=0.2)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p: f"{v/10000:.0f}만" if v >= 10000 else f"{v:.0f}"))

    # x축 날짜 라벨 (하단에만)
    if hasattr(dates.iloc[0], "strftime"):
        tick_positions = list(range(0, len(df), max(len(df) // 6, 1)))
        ax2.set_xticks(tick_positions)
        ax2.set_xticklabels([dates.iloc[i].strftime("%m/%d") for i in tick_positions], fontsize=8)
    else:
        ax2.set_xticks([])

    fig.subplots_adjust(left=0.08, right=0.95, top=0.90, bottom=0.08)

    # BytesIO로 반환
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf
