# 개발 명세서

## 1. 문서 목적

이 문서는 `kiwoom_rest_mock_quant_autotrading_plan.md` 기획서를 기반으로 실제 코드를 작성하기 위한 개발 명세를 정의한다.  
Phase별 구현 대상, 모듈별 상세 설계, DB 스키마, API 연동 규격, 설정 구조를 포함한다.

## 2. 기술 스택 및 의존성

### 런타임

- Python 3.11+
- 가상환경: venv 또는 poetry

### 핵심 의존성

| 패키지 | 용도 | 비고 |
|---|---|---|
| fastapi | REST API 서버 | uvicorn과 함께 사용 |
| uvicorn | ASGI 서버 | |
| httpx | 비동기 HTTP 클라이언트 | 키움 REST API 호출 |
| sqlalchemy | ORM / DB 접근 | 2.0 스타일 사용 |
| alembic | DB 마이그레이션 | |
| pandas | 데이터 분석 / 지표 계산 | |
| numpy | 수치 연산 | |
| pydantic | 데이터 검증 / 설정 관리 | pydantic-settings 포함 |
| apscheduler | 스케줄링 | |
| python-telegram-bot | 텔레그램 봇 | |
| structlog | 구조화 로깅 | |
| ta | 기술지표 라이브러리 | 보조 사용 |
| pytest | 테스트 | pytest-asyncio 포함 |
| aiosqlite | SQLite 비동기 드라이버 | |

### 설정 파일

```
.env                    # 시크릿 (API 키, 토큰, 텔레그램 봇 토큰)
config/settings.yaml    # 전략 파라미터, 리스크 설정, 스케줄 설정
config/scanners/        # 스캐너 조건 YAML 파일들
```

## 3. 디렉터리 구조 상세

```text
project/
  app/
    __init__.py
    main.py                          # FastAPI 앱 진입점
    api/
      __init__.py
      routes_account.py              # 계좌 관련 API
      routes_strategy.py             # 전략 조회/변경 API
      routes_scanner.py              # 스캐너 조회 API
      routes_review.py               # 성과리뷰 API
      routes_health.py               # 헬스체크 API
    core/
      __init__.py
      config.py                      # pydantic-settings 기반 설정
      constants.py                   # 상수 정의
      exceptions.py                  # 공통 예외 클래스
      types.py                       # 공통 타입/Enum 정의
    brokers/
      __init__.py
      base.py                        # 브로커 추상 인터페이스
      kiwoom/
        __init__.py
        auth.py                      # OAuth 토큰 관리
        client.py                    # REST 공통 래퍼
        rate_limiter.py              # API 호출 제한 관리
        account.py                   # 계좌/예수금/잔고 조회
        order.py                     # 주문/정정/취소
        market_data.py               # 차트/시세 조회
        models.py                    # 키움 API 요청/응답 모델
    market/
      __init__.py
      master.py                      # 종목 마스터 관리
      universe.py                    # 유니버스 필터링
      bars.py                        # 일봉/분봉 수집 및 캐시
      indicators.py                  # 기술지표 계산
      calendar.py                    # 거래일 캘린더
    scanners/
      __init__.py
      base.py                        # 스캐너 공통 인터페이스
      dsl.py                         # 조건 DSL 파서
      scoring.py                     # 패턴 점수화
      builtin/
        __init__.py
        volume_breakout.py           # 스캐너 1
        bottom_rebound.py            # 스캐너 2
        ma_recovery.py               # 스캐너 3
        double_bottom.py             # 스캐너 4
        pullback_reentry.py          # 스캐너 5
        first_pullback.py            # 스캐너 6
        c_spot.py                    # 스캐너 7
    strategies/
      __init__.py
      base.py                        # Strategy 베이스 클래스
      momentum_breakout.py           # 전략 1
      pullback_trend.py              # 전략 2
      mean_reversion.py              # 전략 3
      low_volatility_trend.py        # 전략 4
      multi_factor.py                # 전략 5
      registry.py                    # 전략 등록/조회
    execution/
      __init__.py
      engine.py                      # 실행 엔진 메인 루프
      order_builder.py               # 주문 생성
      order_manager.py               # 미체결 관리, 정정/취소
      conflict_resolver.py           # 동시 전략 자금 충돌 중재
    simulation/
      __init__.py
      fill_simulator.py              # 체결 시뮬레이터
      cost_model.py                  # 슬리피지/수수료/세금
    portfolio/
      __init__.py
      manager.py                     # 포지션 관리
      position_sizer.py              # 포지션 sizing
      evaluator.py                   # 평가손익 계산
    risk/
      __init__.py
      manager.py                     # 리스크 통합 관리
      drawdown.py                    # 드로다운 기반 동적 축소
      kill_switch.py                 # 긴급 전체 청산
    scheduler/
      __init__.py
      jobs.py                        # 스케줄 작업 정의
      runner.py                      # APScheduler 실행기
    storage/
      __init__.py
      database.py                    # DB 엔진/세션 관리
      models.py                      # SQLAlchemy 테이블 모델
      repositories/
        __init__.py
        orders.py
        positions.py
        bars.py
        signals.py
        reviews.py
        scanners.py
    backtest/
      __init__.py
      engine.py                      # 백테스트 메인 엔진
      resampler.py                   # 분봉 리샘플링
      portfolio_sim.py               # 가상 포트폴리오
      reporter.py                    # 백테스트 결과 리포트
    monitoring/
      __init__.py
      health.py                      # 헬스체크
      logger.py                      # 로깅 설정
      alerts.py                      # 알림 등급 관리
    recovery/
      __init__.py
      state_sync.py                  # 상태 동기화
      startup_check.py               # 시작 시 점검
    bot/
      __init__.py
      telegram_bot.py                # 텔레그램 봇 메인
      handlers.py                    # 명령 핸들러
      formatters.py                  # 메시지 포맷터
      review_sender.py               # 성과리뷰 발송
  config/
    settings.yaml
    scanners/
      volume_breakout.yaml
      c_spot.yaml
  tests/
    conftest.py
    brokers/
    market/
    strategies/
    execution/
    backtest/
    bot/
    integration/
  scripts/
    init_db.py                       # DB 초기화
    collect_bars.py                  # 과거 데이터 수집 배치
    run_backtest.py                  # 백테스트 CLI
  alembic/
    env.py
    versions/
  .env
  .env.example
  pyproject.toml
```

## 4. Phase별 구현 명세

---

### Phase 1. 기초 인프라

#### 목표

프로젝트 골격 생성, 설정/로깅/DB 기본 구성

#### 구현 대상

##### `app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 키움 API
    kiwoom_app_key: str
    kiwoom_app_secret: str
    kiwoom_account_no: str
    kiwoom_is_mock: bool = True

    # DB
    database_url: str = "sqlite+aiosqlite:///./data/trading.db"

    # 텔레그램
    telegram_bot_token: str
    telegram_chat_id: str

    # 리스크
    max_positions: int = 5
    max_daily_loss_pct: float = 2.0
    per_stock_weight_pct: float = 15.0
    stop_loss_pct: float = 3.0

    # 스케줄
    scan_interval_minutes: int = 5

    # 알림 등급 설정
    alert_level_warning: bool = True
    alert_level_info: bool = False

    class Config:
        env_file = ".env"
```

##### `app/core/constants.py`

```python
# 키움 API 도메인
KIWOOM_REAL_DOMAIN = "https://api.kiwoom.com"
KIWOOM_MOCK_DOMAIN = "https://mockapi.kiwoom.com"

# TR 코드
TR_AUTH = "au10001"
TR_BUY = "kt10000"
TR_SELL = "kt10001"
TR_MODIFY = "kt10002"
TR_CANCEL = "kt10003"
TR_BALANCE = "kt00017"
TR_DEPOSIT = "ka10170"
TR_PENDING = "ka10075"
TR_CHART_MINUTE = "ka10080"
TR_CHART_DAILY = "ka10081"

# 장 시간
MARKET_OPEN = "09:00"
MARKET_CLOSE = "15:30"
MARKET_CLOSE_HALF = "12:30"
PRE_MARKET_START = "08:30"

# 알림 등급
ALERT_CRITICAL = "CRITICAL"
ALERT_WARNING = "WARNING"
ALERT_INFO = "INFO"
```

##### `app/core/types.py`

```python
from enum import Enum

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    BEST = "best"

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
    OPENING = "opening"           # 09:00~09:15
    REGULAR = "regular"           # 09:15~15:00
    CLOSING = "closing"           # 15:00~15:20
    POST_MARKET = "post_market"
    CLOSED = "closed"
```

##### `app/core/exceptions.py`

```python
class TradingError(Exception):
    """자동매매 시스템 기본 예외"""

class AuthError(TradingError):
    """인증/토큰 관련 예외"""

class OrderError(TradingError):
    """주문 관련 예외"""

class RateLimitError(TradingError):
    """API 호출 제한 초과"""

class RiskLimitError(TradingError):
    """리스크 한도 초과"""

class RecoveryError(TradingError):
    """장애 복구 중 오류"""
```

##### `app/storage/database.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)
```

##### `app/monitoring/logger.py`

```python
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
```

#### 완료 기준

- [x] 프로젝트 구조 생성, pyproject.toml 작성
- [x] Settings 로드 시 .env에서 값을 읽어옴
- [x] SQLite DB 파일 생성 및 테이블 마이그레이션 실행
- [x] structlog로 JSON 포맷 로그 출력 확인
- [x] FastAPI 서버 기동 후 `/health` 엔드포인트 200 응답

---

### Phase 2. 브로커 연동

#### 목표

키움 REST API 인증, 계좌 조회, 주문 기능 구현

#### 구현 대상

##### `app/brokers/kiwoom/auth.py`

```python
import asyncio
from datetime import datetime, timedelta

class KiwoomAuth:
    def __init__(self, app_key: str, app_secret: str, base_url: str):
        self._app_key = app_key
        self._app_secret = app_secret
        self._base_url = base_url
        self._token: str | None = None
        self._expires_at: datetime | None = None
        self._refresh_lock = asyncio.Lock()
        self._max_retries = 3

    async def get_token(self) -> str:
        """유효한 토큰 반환. 만료 임박 시 선제적 갱신."""
        if self._is_token_valid():
            return self._token
        return await self._refresh_token()

    def _is_token_valid(self) -> bool:
        if not self._token or not self._expires_at:
            return False
        # 만료 5분 전부터 갱신 대상
        return datetime.now() < self._expires_at - timedelta(minutes=5)

    async def _refresh_token(self) -> str:
        async with self._refresh_lock:
            # 락 획득 후 재확인 (다른 코루틴이 이미 갱신했을 수 있음)
            if self._is_token_valid():
                return self._token
            for attempt in range(self._max_retries):
                try:
                    # POST /oauth2/token (TR: au10001)
                    ...
                    return self._token
                except Exception:
                    if attempt == self._max_retries - 1:
                        raise AuthError("토큰 갱신 실패")
                    await asyncio.sleep(2 ** attempt)
```

##### `app/brokers/kiwoom/rate_limiter.py`

```python
import asyncio
import time

class RateLimiter:
    """토큰 버킷 기반 API 호출 제한 관리"""

    def __init__(self, max_calls_per_second: int = 5):
        self._max_calls = max_calls_per_second
        self._semaphore = asyncio.Semaphore(max_calls_per_second)
        self._call_times: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """호출 슬롯 획득. 제한 초과 시 대기."""
        async with self._lock:
            now = time.monotonic()
            # 1초 이전 호출 제거
            self._call_times = [t for t in self._call_times if now - t < 1.0]
            if len(self._call_times) >= self._max_calls:
                wait = 1.0 - (now - self._call_times[0])
                if wait > 0:
                    await asyncio.sleep(wait)
            self._call_times.append(time.monotonic())

    @property
    def recent_call_count(self) -> int:
        now = time.monotonic()
        return len([t for t in self._call_times if now - t < 1.0])
```

##### `app/brokers/kiwoom/client.py`

```python
import httpx

class KiwoomClient:
    """키움 REST API 공통 래퍼"""

    def __init__(self, auth: KiwoomAuth, rate_limiter: RateLimiter, base_url: str):
        self._auth = auth
        self._rate_limiter = rate_limiter
        self._base_url = base_url
        self._http = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    async def request(self, method: str, path: str, tr_code: str, body: dict) -> dict:
        await self._rate_limiter.acquire()
        token = await self._auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "tr_cd": tr_code,
        }
        response = await self._http.request(method, path, headers=headers, json=body)
        response.raise_for_status()
        return response.json()
```

##### `app/brokers/kiwoom/account.py`

```python
class KiwoomAccount:
    def __init__(self, client: KiwoomClient, account_no: str):
        self._client = client
        self._account_no = account_no

    async def get_deposit(self) -> dict:
        """예수금 조회 (ka10170)"""
        return await self._client.request(
            "POST", "/api/dostk/acnt", "ka10170",
            {"acnt_no": self._account_no}
        )

    async def get_balance(self) -> dict:
        """계좌평가잔고 조회 (kt00017)"""
        return await self._client.request(
            "POST", "/api/dostk/acnt", "kt00017",
            {"acnt_no": self._account_no}
        )

    async def get_pending_orders(self) -> dict:
        """미체결 조회 (ka10075)"""
        return await self._client.request(
            "POST", "/api/dostk/acnt", "ka10075",
            {"acnt_no": self._account_no}
        )
```

##### `app/brokers/kiwoom/order.py`

```python
class KiwoomOrder:
    def __init__(self, client: KiwoomClient, account_no: str):
        self._client = client
        self._account_no = account_no

    async def buy(self, stock_code: str, qty: int, price: int = 0, order_type: str = "market") -> dict:
        """매수 주문 (kt10000)"""
        ...

    async def sell(self, stock_code: str, qty: int, price: int = 0, order_type: str = "market") -> dict:
        """매도 주문 (kt10001)"""
        ...

    async def modify(self, org_order_no: str, qty: int, price: int) -> dict:
        """정정 주문 (kt10002)"""
        ...

    async def cancel(self, org_order_no: str, qty: int) -> dict:
        """취소 주문 (kt10003)"""
        ...
```

##### `app/brokers/kiwoom/market_data.py`

```python
class KiwoomMarketData:
    def __init__(self, client: KiwoomClient):
        self._client = client

    async def get_daily_bars(self, stock_code: str, count: int = 100) -> dict:
        """일봉 차트 조회 (ka10081)"""
        ...

    async def get_minute_bars(self, stock_code: str, interval: int = 1, count: int = 500) -> dict:
        """분봉 차트 조회 (ka10080)"""
        ...
```

#### 완료 기준

- [x] 모의투자 도메인으로 토큰 발급/갱신 성공
- [x] 토큰 선제적 갱신 및 갱신 락 동작 확인
- [x] Rate Limiter가 초당 호출 수를 초과하지 않음
- [x] 예수금/잔고/미체결 조회가 실제 모의투자 계좌 데이터를 반환
- [x] 매수/매도/정정/취소 주문 실행 후 체결 확인
- [x] API 에러 시 적절한 예외 발생 및 로깅

---

### Phase 3. 데이터 레이어

#### 목표

종목 마스터, 일봉/분봉 수집, 유니버스 필터링, 기술지표 계산, 거래일 캘린더

#### 구현 대상

##### `app/market/calendar.py`

```python
class TradingCalendar:
    """거래일 캘린더 관리"""

    async def is_trading_day(self, date: date) -> bool:
        """공휴일, 임시휴장일 제외"""
        ...

    async def is_half_day(self, date: date) -> bool:
        """반일 거래일 여부"""
        ...

    def get_market_close_time(self, date: date) -> time:
        """반일이면 12:30, 아니면 15:30 반환"""
        ...

    async def get_next_trading_day(self, date: date) -> date:
        ...
```

##### `app/market/master.py`

```python
class StockMaster:
    """종목 마스터 관리"""

    async def refresh(self):
        """전 종목 코드/이름/시장구분/종목유형 갱신"""
        ...

    async def get_stock(self, code: str) -> StockInfo:
        ...

    async def get_all_common_stocks(self) -> list[StockInfo]:
        """보통주만 반환 (ETF, ETN, 스팩, 우선주 제외)"""
        ...
```

##### `app/market/universe.py`

```python
class UniverseBuilder:
    """유니버스 필터링"""

    def __init__(self, min_turnover_20d: int = 1_000_000_000, min_price: int = 3000):
        ...

    async def build(self, market_data) -> list[str]:
        """
        필터 조건:
        - KOSPI + KOSDAQ 보통주
        - ETF, ETN, 스팩, 우선주 제외
        - 거래정지/관리종목 제외
        - 최근 20일 평균 거래대금 10억 이상
        - 5일 평균 거래량 기준 미달 제외
        - 주가 3,000원 미만 제외
        """
        ...
```

##### `app/market/bars.py`

```python
class BarCollector:
    """일봉/분봉 수집 및 DB 캐시"""

    async def collect_daily(self, codes: list[str], days: int = 100):
        """야간 배치: 일봉 수집"""
        ...

    async def collect_minute(self, codes: list[str], interval: int = 1):
        """야간 배치: 당일 1분봉 수집 (Rate Limit 고려, 종목 간 간격 설정)"""
        ...

    async def get_daily(self, code: str, days: int) -> pd.DataFrame:
        """DB에서 일봉 조회"""
        ...

    async def get_minute(self, code: str, interval: int, bars: int) -> pd.DataFrame:
        """DB에서 분봉 조회"""
        ...

    async def validate_integrity(self, code: str, date: date) -> list[str]:
        """데이터 무결성 점검: 누락 봉, 이상 OHLCV, 거래일 불일치"""
        ...
```

##### `app/market/indicators.py`

```python
class TechnicalIndicators:
    """기술지표 계산"""

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series: ...

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series: ...

    @staticmethod
    def rsi(series: pd.Series, period: int) -> pd.Series: ...

    @staticmethod
    def atr(df: pd.DataFrame, period: int) -> pd.Series: ...

    @staticmethod
    def bollinger_bands(series: pd.Series, period: int, std: float) -> tuple: ...

    @staticmethod
    def volume_ratio(volume: pd.Series, period: int) -> pd.Series: ...

    @staticmethod
    def ma_slope(series: pd.Series, period: int) -> pd.Series: ...
```

#### 완료 기준

- [x] 거래일 캘린더가 공휴일/반일을 정확히 판별
- [x] 종목 마스터에서 보통주만 필터링
- [x] 유니버스 빌더가 기준에 맞는 종목 리스트 반환
- [x] 일봉/분봉 수집 후 DB에 정상 저장
- [x] 수집된 데이터에 대한 무결성 점검 통과
- [x] 기술지표 계산 결과가 기대값과 일치 (단위 테스트)

---

### Phase 4. 전략 엔진

#### 목표

전략 공통 인터페이스, 전략 5종 구현, 전략 선택/등록 기능

#### 구현 대상

##### `app/strategies/base.py`

```python
from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    name: str
    timeframe: str              # "1m", "3m", "5m", "10m", "15m"
    warmup_bars: int            # 지표 계산에 필요한 최소 과거 봉 수
    max_positions: int
    supports_overnight: bool

    @abstractmethod
    def prepare_features(self, bars: pd.DataFrame) -> pd.DataFrame:
        """지표 계산 및 피처 생성"""
        ...

    @abstractmethod
    def on_bar(self, current_time, data_slice: pd.DataFrame, portfolio, account_state) -> list[Signal]:
        """새로운 봉 도착 시 호출. 시그널 리스트 반환."""
        ...

    @abstractmethod
    def generate_orders(self, signals: list[Signal], portfolio, account_state) -> list[Order]:
        """시그널 기반 주문 생성"""
        ...


@dataclass
class Signal:
    stock_code: str
    action: SignalAction         # ENTRY / EXIT / HOLD
    side: OrderSide | None       # BUY / SELL
    reason: str
    score: float = 0.0
    target_price: float | None = None
    stop_price: float | None = None
```

##### `app/strategies/registry.py`

```python
class StrategyRegistry:
    _strategies: dict[str, type[Strategy]] = {}

    @classmethod
    def register(cls, strategy_cls: type[Strategy]):
        cls._strategies[strategy_cls.name] = strategy_cls

    @classmethod
    def get(cls, name: str) -> type[Strategy]:
        ...

    @classmethod
    def list_all(cls) -> list[str]:
        ...
```

##### 전략별 핵심 파라미터

| 전략 | 클래스명 | timeframe | warmup_bars | max_positions | supports_overnight |
|---|---|---|---|---|---|
| 1. 단기 모멘텀 돌파 | MomentumBreakout | 5m | 80 | 5 | False |
| 2. 눌림목 추세추종 | PullbackTrend | 10m | 60 | 5 | True |
| 3. 평균회귀 과매도 반등 | MeanReversion | 5m | 40 | 5 | False |
| 4. 저변동성 추세 지속 | LowVolTrend | 15m | 80 | 5 | True |
| 5. 멀티팩터 랭킹 | MultiFactor | 5m | 60 | 5 | True |

#### 완료 기준

- [x] 5개 전략이 모두 Strategy 인터페이스를 구현
- [x] StrategyRegistry에 5개 전략 등록/조회 가능
- [x] 각 전략의 on_bar() 호출 시 Signal 리스트 반환
- [x] 전략별 단위 테스트: 과거 데이터 기반으로 시그널 생성 확인

---

### Phase 4-1. 스캐너 엔진

#### 목표

사용자 조건 DSL 파서, 기본 스캐너 7종, 점수화 로직

#### 구현 대상

##### `app/scanners/base.py`

```python
class Scanner(ABC):
    name: str
    market: str = "KRX"
    timeframe: str = "5m"

    @abstractmethod
    async def scan(self, market_data, filters: dict) -> list[ScanResult]:
        ...

@dataclass
class ScanResult:
    stock_code: str
    stock_name: str
    score: float
    reasons: list[str]
    scanned_at: datetime
```

##### `app/scanners/dsl.py`

```python
class ScannerDSL:
    """YAML 조건 파서"""

    @staticmethod
    def load(path: str) -> ScannerConfig:
        """YAML 파일에서 스캐너 조건 로드"""
        ...

    @staticmethod
    def evaluate(config: ScannerConfig, market_data) -> list[ScanResult]:
        """조건 평가 및 결과 반환"""
        ...
```

#### 완료 기준

- [x] YAML 조건 파일을 파싱해 스캐너 실행 가능
- [x] 7개 내장 스캐너가 각각 결과 반환
- [x] 점수 기반 정렬 동작 확인
- [x] 텔레그램 `/scan` 명령으로 결과 조회 가능

---

### Phase 5. 실행 엔진

#### 목표

주문 생성, 포지션 sizing, 리스크 관리, 스케줄링 통합

#### 구현 대상

##### `app/execution/engine.py`

```python
class ExecutionEngine:
    """자동매매 메인 실행 루프"""

    async def run_cycle(self):
        """
        1주기 실행 흐름:
        1. 현재 시장 페이즈 확인
        2. 계좌 상태 조회
        3. 미체결 주문 점검/정정/취소
        4. 보유 포지션 리스크 점검 (손절/익절/시간청산)
        5. 전략 on_bar() 호출 -> 시그널 수집
        6. 자금 충돌 중재
        7. 리스크 한도 점검
        8. 주문 생성 및 실행
        9. 결과 저장 및 알림
        """
        ...
```

##### `app/execution/conflict_resolver.py`

```python
class ConflictResolver:
    """동시 전략 자금 충돌 중재"""

    def resolve(self, orders: list[Order], available_cash: float, positions: list) -> list[Order]:
        """
        규칙:
        - 동일 종목 중복 매수 금지 (먼저 발생한 시그널 우선)
        - 가용 자금 초과 시 시그널 점수 높은 순으로 선별
        - 전략별 최대 배분 비중 초과 방지
        """
        ...
```

##### `app/portfolio/position_sizer.py`

```python
class PositionSizer:
    """포지션 sizing"""

    def equal_weight(self, available_cash: float, max_positions: int, price: float) -> int:
        """동일가중: 가용자금 / 최대종목수 / 현재가"""
        ...

    def volatility_inverse(self, available_cash: float, atr: float, price: float) -> int:
        """변동성 역가중"""
        ...
```

##### `app/risk/manager.py`

```python
class RiskManager:
    async def check_entry_allowed(self, portfolio, account_state) -> tuple[bool, str]:
        """
        진입 허용 여부 점검:
        - 일일 손실 한도 초과 여부
        - 연속 손실 횟수 초과 여부
        - 최대 포지션 수 초과 여부
        - 장 마감 직전 진입 제한
        - 드로다운 기반 비중 축소 적용
        """
        ...

    async def check_exit_required(self, position, current_price) -> tuple[bool, str]:
        """
        강제 청산 여부 점검:
        - 손절 가격 도달
        - 익절 가격 도달
        - 보유 기간 초과
        - 추세 이탈
        """
        ...
```

##### `app/risk/drawdown.py`

```python
class DrawdownManager:
    """드로다운 기반 동적 포지션 축소"""

    def get_weight_multiplier(self, current_mdd_pct: float) -> float:
        """
        MDD 1% 도달: 0.5 (비중 50% 축소)
        MDD 2% 도달: 0.0 (신규 진입 중지)
        그 외: 1.0
        """
        ...
```

##### `app/risk/kill_switch.py`

```python
class KillSwitch:
    async def execute(self, order_client, portfolio):
        """
        1. 모든 미체결 주문 취소
        2. 모든 보유 포지션 시장가 매도
        3. 스케줄러 정지
        4. 텔레그램 CRITICAL 알림
        """
        ...
```

##### `app/scheduler/jobs.py`

```python
class TradingJobs:
    async def pre_market(self):
        """08:30 - 토큰 확보, 계좌 조회, 유니버스 준비, 거래일 확인"""
        ...

    async def scan_cycle(self):
        """09:15~15:00 - 5분 주기 스캔 및 주문"""
        ...

    async def pending_check(self):
        """장중 1분 주기 - 미체결 점검"""
        ...

    async def market_close(self):
        """15:00~15:20 - 당일 청산 전략 포지션 정리"""
        ...

    async def post_market(self):
        """15:30 이후 - 로그 저장, 성과 리포트, 분봉 수집"""
        ...

    async def daily_review(self):
        """장 종료 후 - 일간 성과리뷰 생성 및 발송"""
        ...

    async def weekly_review(self):
        """주간 마지막 거래일 - 주간 성과리뷰"""
        ...

    async def monthly_review(self):
        """월말 마지막 거래일 - 월간 성과리뷰"""
        ...
```

#### 완료 기준

- [x] ExecutionEngine.run_cycle()이 한 주기 정상 실행
- [x] 포지션 sizing 계산 결과가 리스크 한도 내
- [x] 손절/익절/시간청산 트리거 동작
- [x] 동시 전략 자금 충돌 시 우선순위 규칙 적용
- [x] 드로다운 비중 축소 정상 동작
- [x] Kill Switch 실행 후 전 포지션 청산 확인
- [x] 스케줄러가 장 시간에 맞춰 작업 실행

---

### Phase 6. 운영 보조

#### 목표

텔레그램 봇, 알림, 성과리뷰, 대시보드, 장애 복구

#### 구현 대상

##### `app/bot/handlers.py`

```python
class BotHandlers:
    async def cmd_status(self, update, context): ...
    async def cmd_strategies(self, update, context): ...
    async def cmd_strategy_set(self, update, context): ...
    async def cmd_start_bot(self, update, context): ...
    async def cmd_stop_bot(self, update, context): ...
    async def cmd_positions(self, update, context): ...
    async def cmd_orders_today(self, update, context): ...
    async def cmd_scan(self, update, context): ...
    async def cmd_review(self, update, context): ...
    async def cmd_kill_all(self, update, context): ...
    async def cmd_health(self, update, context): ...
```

##### `app/monitoring/alerts.py`

```python
class AlertManager:
    def __init__(self, bot, settings):
        self._bot = bot
        self._settings = settings

    async def send(self, level: AlertLevel, message: str):
        """등급별 필터링 후 발송"""
        if level == AlertLevel.CRITICAL:
            await self._bot.send(message)
        elif level == AlertLevel.WARNING and self._settings.alert_level_warning:
            await self._bot.send(message)
        elif level == AlertLevel.INFO and self._settings.alert_level_info:
            await self._bot.send(message)
```

##### `app/recovery/startup_check.py`

```python
class StartupCheck:
    async def run(self):
        """
        시작 시 점검 순서:
        1. DB 연결 확인
        2. 토큰 유효성 확인 (만료 시 재발급)
        3. 브로커 측 미체결 주문 조회 -> 로컬 DB와 비교 동기화
        4. 브로커 측 잔고 조회 -> 로컬 positions과 비교 동기화
        5. 불일치 항목 로그 기록 및 CRITICAL 알림
        6. 동기화 완료 후 스케줄러 시작 허용
        """
        ...
```

##### `app/monitoring/health.py`

```python
class HealthCheck:
    async def check(self) -> dict:
        return {
            "status": "ok" | "degraded" | "error",
            "api_connection": bool,
            "token_valid": bool,
            "token_expires_in_minutes": float,
            "scheduler_running": bool,
            "last_scan_at": datetime | None,
            "last_order_at": datetime | None,
            "active_strategy": str,
            "open_positions": int,
            "daily_pnl_pct": float,
        }
```

#### 완료 기준

- [x] 텔레그램 봇 모든 명령 응답 확인
- [x] 알림 등급별 필터링 동작
- [x] 일/주/월 성과리뷰 생성 및 텔레그램 발송
- [x] 성과리뷰에 벤치마크 대비 수익률 포함
- [x] 성과리뷰에 전략 이력 포함
- [x] 장애 복구 시 상태 동기화 정상 수행
- [x] 헬스체크 엔드포인트 응답 확인

---

### Phase 7. 백테스트 엔진

#### 목표

분봉 기반 이벤트 재생 엔진, 멀티전략 지원, 결과 리포트

#### 구현 대상

##### `app/backtest/engine.py`

```python
class BacktestEngine:
    def __init__(self, strategies: list[Strategy], start_date, end_date, initial_cash: float):
        ...

    async def run(self) -> BacktestResult:
        """
        실행 흐름:
        1. 기간 내 거래일 목록 생성
        2. 거래일별 1분봉 로드
        3. 전략별 timeframe으로 리샘플링
        4. 봉 단위 순차 재생 -> strategy.on_bar() 호출
        5. 시그널 -> 주문 시뮬레이션 (다음 봉 시가 체결)
        6. 포트폴리오 업데이트
        7. 결과 집계
        """
        ...
```

##### `app/backtest/resampler.py`

```python
class BarResampler:
    @staticmethod
    def resample(minute_bars: pd.DataFrame, target_interval: int) -> pd.DataFrame:
        """1분봉 -> N분봉 리샘플링. 거래일 경계 기준 정확히 재구성."""
        ...
```

##### `app/backtest/reporter.py`

```python
class BacktestReporter:
    def generate(self, result: BacktestResult) -> dict:
        return {
            "cagr": ...,
            "mdd": ...,
            "sharpe_ratio": ...,
            "profit_factor": ...,
            "win_rate": ...,
            "avg_profit_loss_ratio": ...,
            "turnover": ...,
            "total_trades": ...,
            "monthly_returns": ...,
            "equity_curve": ...,
            "benchmark_comparison": ...,
            "strategy_correlation": ...,
        }
```

#### 완료 기준

- [x] 단일 전략 백테스트 실행 및 결과 확인
- [x] 멀티 전략 동시 백테스트 실행 및 자금 배분 반영
- [x] 슬리피지/수수료/세금 반영 확인
- [x] 분봉 리샘플링 정확도 검증
- [x] 백테스트 결과가 DB에 저장 (backtest_runs, backtest_trades, backtest_equity_curve)
- [x] 벤치마크 대비 성과 포함

## 5. DB 스키마

### 테이블 DDL

```sql
-- 계좌
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no TEXT NOT NULL UNIQUE,
    is_mock BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 포지션
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(id),
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    strategy_name TEXT,
    qty INTEGER NOT NULL DEFAULT 0,
    avg_price REAL NOT NULL DEFAULT 0,
    current_price REAL,
    unrealized_pnl REAL,
    entry_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 주문
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES accounts(id),
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    strategy_name TEXT,
    side TEXT NOT NULL,                -- buy / sell
    order_type TEXT NOT NULL,          -- market / limit / best
    qty INTEGER NOT NULL,
    price REAL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending / filled / partial / cancelled / rejected
    broker_order_no TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 체결
CREATE TABLE fills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    stock_code TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    price REAL NOT NULL,
    slippage REAL,                     -- 주문가 대비 체결가 괴리
    commission REAL,
    tax REAL,
    fill_time_ms INTEGER,              -- 주문 접수 -> 체결 소요시간(ms)
    filled_at TIMESTAMP
);

-- 일봉
CREATE TABLE daily_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL, high REAL, low REAL, close REAL,
    volume INTEGER,
    turnover REAL,
    UNIQUE(stock_code, date)
);

-- 분봉
CREATE TABLE minute_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    interval INTEGER NOT NULL DEFAULT 1,  -- 1분봉
    open REAL, high REAL, low REAL, close REAL,
    volume INTEGER,
    turnover REAL,
    UNIQUE(stock_code, datetime, interval)
);

-- 리샘플링 봉
CREATE TABLE resampled_bars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    interval INTEGER NOT NULL,            -- 3, 5, 10, 15
    open REAL, high REAL, low REAL, close REAL,
    volume INTEGER,
    UNIQUE(stock_code, datetime, interval)
);

-- 시그널
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    action TEXT NOT NULL,                  -- entry / exit
    side TEXT,
    score REAL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 전략 실행 기록
CREATE TABLE strategy_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    status TEXT DEFAULT 'running',
    params_json TEXT
);

-- 전략 선택 이력
CREATE TABLE strategy_selections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    selected_at TIMESTAMP NOT NULL,
    released_at TIMESTAMP,
    selected_by TEXT NOT NULL,             -- telegram / dashboard / system
    reason TEXT
);

-- 스캐너 규칙
CREATE TABLE scanner_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    config_yaml TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스캐너 실행 기록
CREATE TABLE scanner_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scanner_name TEXT NOT NULL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result_count INTEGER DEFAULT 0
);

-- 스캐너 결과
CREATE TABLE scanner_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES scanner_runs(id),
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    score REAL,
    reasons TEXT
);

-- 텔레그램 메시지 이력
CREATE TABLE telegram_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direction TEXT NOT NULL,               -- inbound / outbound
    command TEXT,
    message TEXT,
    alert_level TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 성과리뷰
CREATE TABLE performance_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_type TEXT NOT NULL,             -- daily / weekly / monthly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    strategy_names TEXT,
    strategy_changes_json TEXT,
    realized_pnl REAL,
    unrealized_pnl REAL,
    total_return_pct REAL,
    mdd_pct REAL,
    total_trades INTEGER,
    win_rate REAL,
    avg_profit_loss_ratio REAL,
    benchmark_return_pct REAL,
    excess_return_pct REAL,
    report_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 백테스트 실행 기록
CREATE TABLE backtest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_names TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_cash REAL,
    timeframe TEXT,
    params_json TEXT,
    result_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 백테스트 거래
CREATE TABLE backtest_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES backtest_runs(id),
    strategy_name TEXT,
    stock_code TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    entry_price REAL,
    exit_price REAL,
    qty INTEGER,
    pnl REAL,
    mfe REAL,                              -- Maximum Favorable Excursion
    mae REAL                               -- Maximum Adverse Excursion
);

-- 백테스트 자산곡선
CREATE TABLE backtest_equity_curve (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES backtest_runs(id),
    date DATE NOT NULL,
    equity REAL NOT NULL,
    daily_return_pct REAL
);

-- 일일 리포트
CREATE TABLE daily_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    report_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 거래일 캘린더
CREATE TABLE trading_calendar (
    date DATE PRIMARY KEY,
    is_trading_day BOOLEAN NOT NULL DEFAULT TRUE,
    is_half_day BOOLEAN NOT NULL DEFAULT FALSE,
    close_time TEXT,                        -- "15:30" or "12:30"
    note TEXT
);

-- 전략 파라미터 프로파일
CREATE TABLE strategy_param_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    profile_name TEXT NOT NULL,
    params_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_name, profile_name)
);

-- 슬리피지 통계
CREATE TABLE slippage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    stock_code TEXT,
    avg_slippage_pct REAL,
    max_slippage_pct REAL,
    unfilled_rate REAL,                    -- 미체결 비율
    avg_fill_time_ms REAL,
    sample_count INTEGER,
    UNIQUE(date, stock_code)
);
```

### 인덱스

```sql
CREATE INDEX idx_positions_account ON positions(account_id);
CREATE INDEX idx_orders_account_status ON orders(account_id, status);
CREATE INDEX idx_orders_stock_code ON orders(stock_code);
CREATE INDEX idx_fills_order ON fills(order_id);
CREATE INDEX idx_daily_bars_code_date ON daily_bars(stock_code, date);
CREATE INDEX idx_minute_bars_code_dt ON minute_bars(stock_code, datetime);
CREATE INDEX idx_signals_strategy_time ON signals(strategy_name, created_at);
CREATE INDEX idx_strategy_selections_time ON strategy_selections(selected_at);
CREATE INDEX idx_scanner_results_run ON scanner_results(run_id);
CREATE INDEX idx_performance_reviews_type_period ON performance_reviews(review_type, period_start);
CREATE INDEX idx_backtest_trades_run ON backtest_trades(run_id);
CREATE INDEX idx_backtest_equity_run ON backtest_equity_curve(run_id);
CREATE INDEX idx_slippage_date ON slippage_stats(date);
```

## 6. API 연동 규격 요약

### 공통 헤더

```
Authorization: Bearer {access_token}
Content-Type: application/json
tr_cd: {TR코드}
```

### 주요 엔드포인트 / TR 매핑

| 기능 | 메서드 | 경로 | TR코드 |
|---|---|---|---|
| 토큰 발급 | POST | /oauth2/token | au10001 |
| 예수금 조회 | POST | /api/dostk/acnt | ka10170 |
| 잔고 조회 | POST | /api/dostk/acnt | kt00017 |
| 미체결 조회 | POST | /api/dostk/acnt | ka10075 |
| 매수 주문 | POST | /api/dostk/ordr | kt10000 |
| 매도 주문 | POST | /api/dostk/ordr | kt10001 |
| 정정 주문 | POST | /api/dostk/ordr | kt10002 |
| 취소 주문 | POST | /api/dostk/ordr | kt10003 |
| 분봉 차트 | POST | /api/dostk/chart | ka10080 |
| 일봉 차트 | POST | /api/dostk/chart | ka10081 |

### 도메인

- 모의투자: `https://mockapi.kiwoom.com`
- 실거래: `https://api.kiwoom.com`

### 에러 처리 규칙

| HTTP 상태 | 대응 |
|---|---|
| 401 | 토큰 갱신 후 재시도 (최대 1회) |
| 429 | Rate Limit 대기 후 재시도 (지수 백오프) |
| 500 | 3회 재시도 후 실패 시 CRITICAL 알림 |
| 그 외 4xx | 요청 파라미터 로깅 후 OrderError 발생 |

## 7. 모듈 간 호출 흐름

### 장중 스캔 1주기

```
scheduler.scan_cycle()
  → recovery.startup_check (최초 1회)
  → market.calendar.is_trading_day()
  → brokers.kiwoom.account.get_balance()
  → brokers.kiwoom.account.get_pending_orders()
  → execution.order_manager.check_pending()
  → market.bars.get_minute() (유니버스 종목)
  → strategies[active].on_bar()
  → risk.manager.check_entry_allowed()
  → risk.drawdown.get_weight_multiplier()
  → execution.conflict_resolver.resolve()
  → portfolio.position_sizer.equal_weight()
  → brokers.kiwoom.order.buy() / sell()
  → storage.repositories.orders.save()
  → monitoring.alerts.send()
```

### 장애 복구 흐름

```
recovery.startup_check.run()
  → storage.database.check_connection()
  → brokers.kiwoom.auth.get_token()
  → brokers.kiwoom.account.get_pending_orders()
  → storage.repositories.orders.get_pending()
  → 비교 → 불일치 시 동기화 + CRITICAL 알림
  → brokers.kiwoom.account.get_balance()
  → storage.repositories.positions.get_all()
  → 비교 → 불일치 시 동기화 + CRITICAL 알림
  → scheduler.runner.start()
```

### 텔레그램 명령 흐름

```
bot.telegram_bot (수신)
  → bot.handlers.cmd_xxx()
    → 해당 모듈 호출 (strategies, portfolio, execution, scanners, monitoring)
  → bot.formatters.format_xxx()
  → bot.telegram_bot (응답 발송)
```
