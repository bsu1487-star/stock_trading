"""텔레그램 인라인 키보드 정의"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


# ── 메인 메뉴 (하단 고정 키보드) ──

MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("/status"), KeyboardButton("/positions")],
        [KeyboardButton("/strategies"), KeyboardButton("/scan")],
        [KeyboardButton("/review"), KeyboardButton("/health")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


# ── 전략 선택 인라인 버튼 ──

def strategy_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("멀티팩터 (추천)", callback_data="strat:multi_factor")],
        [InlineKeyboardButton("모멘텀 돌파", callback_data="strat:momentum_breakout")],
        [InlineKeyboardButton("눌림목 추세", callback_data="strat:pullback_trend")],
        [InlineKeyboardButton("평균회귀 반등", callback_data="strat:mean_reversion")],
        [InlineKeyboardButton("저변동성 추세", callback_data="strat:low_volatility_trend")],
    ]
    return InlineKeyboardMarkup(buttons)


# ── 스캐너 한글 이름 매핑 ──

SCANNER_NAMES = {
    "volume_breakout": "거래량 돌파",
    "bottom_rebound": "저점 반등",
    "ma_recovery": "이평 회복",
    "double_bottom": "이중바닥",
    "pullback_reentry": "눌림 재상승",
    "first_pullback": "첫 조정",
    "c_spot": "C자리",
}


def get_scanner_label(scanner_id: str) -> str:
    return SCANNER_NAMES.get(scanner_id, scanner_id)


# ── 스캐너 선택 인라인 버튼 ──

def scanner_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("거래량 돌파", callback_data="scan:volume_breakout"),
            InlineKeyboardButton("저점 반등", callback_data="scan:bottom_rebound"),
        ],
        [
            InlineKeyboardButton("이평 회복", callback_data="scan:ma_recovery"),
            InlineKeyboardButton("이중바닥", callback_data="scan:double_bottom"),
        ],
        [
            InlineKeyboardButton("눌림 재상승", callback_data="scan:pullback_reentry"),
            InlineKeyboardButton("첫 조정", callback_data="scan:first_pullback"),
        ],
        [InlineKeyboardButton("C자리", callback_data="scan:c_spot")],
    ]
    return InlineKeyboardMarkup(buttons)


# ── 성과리뷰 인라인 버튼 ──

def review_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("일간", callback_data="review:daily"),
            InlineKeyboardButton("주간", callback_data="review:weekly"),
            InlineKeyboardButton("월간", callback_data="review:monthly"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# ── 봇 제어 인라인 버튼 ──

def control_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("봇 시작", callback_data="ctrl:start"),
            InlineKeyboardButton("봇 정지", callback_data="ctrl:stop"),
        ],
        [InlineKeyboardButton("긴급 청산 (KILL)", callback_data="ctrl:kill")],
    ]
    return InlineKeyboardMarkup(buttons)


# ── Kill 확인 버튼 ──

def kill_confirm_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton("확인 - 전체 청산", callback_data="kill:confirm"),
            InlineKeyboardButton("취소", callback_data="kill:cancel"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
