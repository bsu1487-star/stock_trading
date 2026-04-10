# 키움 자동매매 시스템

키움증권 REST API 기반 국내 주식 모의투자 자동매매 프로그램.  
퀀트 전략 5종, 종목 스캐너 7종, 백테스트 엔진, 텔레그램 봇을 포함한다.

## 요구사항

- Python 3.11 이상
- 키움증권 OpenAPI 계정 (모의투자)
- 텔레그램 봇 (선택)

---

## 설치

```bash
git clone <repo-url> && cd kiwoom
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

---

## 환경 설정 (.env)

`.env.example`을 복사해서 `.env`를 만들고 아래 값을 채운다.

```bash
cp .env.example .env
```

### 필수 항목

| 변수 | 설명 | 발급 방법 |
|---|---|---|
| `KIWOOM_APP_KEY` | 키움 OpenAPI 앱 키 | 아래 "키움 API 키 발급" 참조 |
| `KIWOOM_APP_SECRET` | 키움 OpenAPI 앱 시크릿 | 아래 "키움 API 키 발급" 참조 |
| `KIWOOM_ACCOUNT_NO` | 모의투자 계좌번호 | 아래 "모의투자 계좌" 참조 |

### 선택 항목

| 변수 | 설명 | 기본값 |
|---|---|---|
| `KIWOOM_IS_MOCK` | 모의투자 여부 (`true`/`false`) | `true` |
| `DATABASE_URL` | DB 경로 | `sqlite+aiosqlite:///./data/trading.db` |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | (없으면 봇 비활성) |
| `TELEGRAM_CHAT_ID` | 텔레그램 채팅 ID | (없으면 알림 비활성) |

### .env 예시

```env
KIWOOM_APP_KEY=abc123def456
KIWOOM_APP_SECRET=xyz789secret
KIWOOM_ACCOUNT_NO=8000000011
KIWOOM_IS_MOCK=true

DATABASE_URL=sqlite+aiosqlite:///./data/trading.db

TELEGRAM_BOT_TOKEN=7000000000:AAF_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

---

## 키움 API 키 발급

1. [키움 OpenAPI 사이트](https://openapi.kiwoom.com) 접속
2. 회원가입 또는 로그인 (키움증권 계정 필요)
3. 좌측 메뉴 **"앱 등록"** 클릭
4. 앱 이름 입력 후 등록
5. 등록된 앱의 **App Key**와 **App Secret**을 확인
6. 이 값을 `.env`의 `KIWOOM_APP_KEY`, `KIWOOM_APP_SECRET`에 입력

> 주의: App Secret은 발급 시 한 번만 표시된다. 반드시 바로 복사해서 저장할 것.

## 모의투자 계좌

1. [키움증권 영웅문](https://www.kiwoom.com) 또는 영웅문4 HTS에 로그인
2. **모의투자 신청** 메뉴에서 모의투자 계좌 개설
3. 발급된 **모의투자 계좌번호**를 `.env`의 `KIWOOM_ACCOUNT_NO`에 입력

> 모의투자 계좌는 실계좌와 별도이며, KRX 종목만 거래 가능하다.

## 텔레그램 봇 설정

텔레그램 봇은 **선택사항**이다. 설정하지 않아도 시스템은 정상 동작한다.

### 봇 토큰 발급

1. 텔레그램에서 [@BotFather](https://t.me/BotFather) 검색 후 대화 시작
2. `/newbot` 입력
3. 봇 이름과 username을 입력 (username은 `_bot`으로 끝나야 함)
4. 발급된 **토큰**을 `.env`의 `TELEGRAM_BOT_TOKEN`에 입력

### 채팅 ID 확인

1. 만든 봇과 대화방에서 아무 메시지 전송
2. 브라우저에서 아래 URL 접속 (토큰 부분을 실제 값으로 교체):
   ```
   https://api.telegram.org/bot{봇토큰}/getUpdates
   ```
3. 응답 JSON에서 `"chat":{"id":123456789}` 부분의 숫자를 확인
4. 이 값을 `.env`의 `TELEGRAM_CHAT_ID`에 입력

---

## 실행

### 서버 실행

```bash
uvicorn app.main:app --reload
```

헬스체크 확인:

```bash
curl http://localhost:8000/health
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 프로젝트 구조

```
app/
├── core/           설정, 상수, 타입, 예외
├── brokers/kiwoom/ 키움 인증, Rate Limiter, REST 클라이언트, 계좌, 주문, 시세
├── market/         거래일 캘린더, 종목 마스터, 유니버스 필터, 봉 수집, 기술지표
├── strategies/     전략 베이스 클래스 + 전략 5종 + 레지스트리
├── scanners/       스캐너 7종 + YAML DSL 파서 + 점수화
├── execution/      자동매매 실행 엔진, 동시 전략 자금 충돌 중재
├── portfolio/      포지션 관리, 포지션 sizing
├── risk/           리스크 매니저, 드로다운 동적 축소, Kill Switch
├── scheduler/      APScheduler 기반 장전/장중/장후 스케줄링
├── backtest/       분봉 리샘플링, 이벤트 재생 백테스트 엔진, 리포터
├── simulation/     슬리피지/수수료/세금 체결 비용 모델
├── monitoring/     구조화 로깅, 알림(3등급), 헬스체크
├── recovery/       장애 복구, 시작 시 브로커 상태 동기화
├── bot/            텔레그램 봇, 명령 핸들러, 메시지 포맷터
└── storage/        SQLAlchemy 모델 (21 테이블), DB 세션 관리
```

## 탑재 전략

| # | 이름 | 클래스 | 타임프레임 | 설명 |
|---|---|---|---|---|
| 1 | 단기 모멘텀 돌파 | `MomentumBreakout` | 5분 | N일 고가 돌파 + 거래량 급증 종목 추종 |
| 2 | 눌림목 추세추종 | `PullbackTrend` | 10분 | 상승 추세 종목의 단기 조정 후 반등 포착 |
| 3 | 평균회귀 과매도 반등 | `MeanReversion` | 5분 | RSI 과매도 + 급락 종목 단기 반등 매매 |
| 4 | 저변동성 추세 지속 | `LowVolTrend` | 15분 | 저변동성 우상향 종목 추세 추종 |
| 5 | 멀티팩터 랭킹 | `MultiFactor` | 5분 | 모멘텀/거래대금/추세/변동성 복합 점수 기반 |

## 탑재 스캐너

| # | 이름 | 설명 |
|---|---|---|
| 1 | 거래량 돌파 | 거래량 급증 + 가격 돌파 |
| 2 | 저점 반등 | RSI 과매도 + 낙폭 과대 |
| 3 | 이평선 회복 | 20일선 상향 돌파 |
| 4 | 이중바닥 | 이중바닥 패턴 + 넥라인 접근 |
| 5 | 눌림 재상승 | 상승추세 눌림 후 거래량 재확대 |
| 6 | 첫 조정 | 당일 급등 후 첫 되돌림 지지 |
| 7 | C자리 | 선행 급등 → 눌림 → 재출발 패턴 |

## 텔레그램 명령어

| 명령 | 설명 |
|---|---|
| `/status` | 봇 상태, 계좌 요약, 현재 전략 |
| `/strategies` | 사용 가능한 전략 목록 |
| `/strategy set <name>` | 전략 변경 |
| `/positions` | 보유 종목 조회 |
| `/orders_today` | 당일 주문/체결 |
| `/scan <name>` | 스캐너 실행 (breakout, reversal, cspot 등) |
| `/review daily` | 당일 성과리뷰 |
| `/review weekly` | 주간 성과리뷰 |
| `/health` | 시스템 헬스체크 |
| `/kill_all` | 긴급 전체 청산 + 봇 정지 |

## 리스크 설정

`.env`에서 추가로 조정할 수 있는 리스크 파라미터:

| 변수 | 설명 | 기본값 |
|---|---|---|
| `MAX_POSITIONS` | 최대 동시 보유 종목 수 | 5 |
| `MAX_DAILY_LOSS_PCT` | 일일 최대 손실 (%) | 2.0 |
| `PER_STOCK_WEIGHT_PCT` | 종목당 투자 비중 (%) | 15.0 |
| `STOP_LOSS_PCT` | 종목별 손절 (%) | 3.0 |
| `TAKE_PROFIT_PCT` | 종목별 익절 (%) | 5.0 |
| `MDD_REDUCE_THRESHOLD_PCT` | MDD 비중 축소 임계치 (%) | 1.0 |
| `MDD_STOP_THRESHOLD_PCT` | MDD 진입 중지 임계치 (%) | 2.0 |
| `SCAN_INTERVAL_MINUTES` | 스캔 주기 (분) | 5 |
| `ALERT_LEVEL_WARNING` | WARNING 알림 수신 | true |
| `ALERT_LEVEL_INFO` | INFO 알림 수신 | false |
| `API_MAX_CALLS_PER_SECOND` | API 초당 최대 호출 수 | 5 |

---

## 문서

- [기획서](docs/kiwoom_rest_mock_quant_autotrading_plan.md) - 시스템 전체 기획
- [개발 명세서](docs/development_spec.md) - Phase별 구현 상세, DB 스키마, API 규격
- [검증 계획서](docs/verification_plan.md) - 단위/통합/백테스트/전진검증/실전전환 계획
