# my-ledger

개인용 로컬 AI 가계부 시스템. 카드/은행 CSV를 Import하여 SQLite에 저장하고, 자동으로
카테고리를 분류한 뒤, MCP Server를 통해 Claude에서 자연어로 조회/분석합니다.

모든 데이터는 로컬 PC(`data/ledger.db`)에만 저장되며, 외부 서버로 전송되지 않습니다.

## 요구 사항

- Python 3.12 (Homebrew: `brew install python@3.12`)
- SQLite (macOS 기본 제공)

## 빠른 실행 / 종료

```bash
./start.sh   # venv·node_modules 자동 설치 → DB 마이그레이션 → 프론트 빌드(변경 시) → 백엔드 실행 → 브라우저 열기
./stop.sh    # 백엔드 종료
```

백엔드 PID/로그는 `.run/`에 저장됩니다 (`.run/uvicorn.log`).

## 셋업

```bash
cd backend
python3.12 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## DB 초기화

Alembic 마이그레이션을 적용하고 기본 카테고리를 시드합니다. `data/ledger.db`가 없으면
새로 생성됩니다.

```bash
cd backend
./.venv/bin/python -m app.core.init_db
```

## DB 스키마 변경 (Alembic)

`backend/app/models/`의 모델을 수정한 뒤:

```bash
cd backend
./.venv/bin/alembic revision --autogenerate -m "설명"
./.venv/bin/alembic upgrade head
```

## CSV/Excel Import

카드사 다운로드 파일(확장자와 무관하게 실제 xlsx 또는 HTML 형식을 자동 감지)을 `imports/`에 넣고:

```bash
cd backend
./.venv/bin/python -m app.services.import_service ../imports/파일명.xlsx
```

같은 파일을 다시 돌려도 이미 저장된 거래는 건너뜁니다(fingerprint 기반 중복 방지).
현재 지원: 삼성카드(국내/해외), 신한카드(카드이용내역조회 통합), 신한체크 대중교통 이용내역, 현대카드(국내),
신한은행 거래내역조회 PDF, 수동 전사 CSV(앱 캡처·종이 명세서만 있는 은행용, 예: 기업은행).

수동 전사 CSV는 첫 줄이 `# my-ledger manual bank statement v1` 이고 `# institution:` 헤더와
`date,time,counterparty,amount,balance,type,memo` 컬럼을 가집니다 (amount는 부호 있는 금액, type은
EXPENSE/INCOME/TRANSFER 또는 빈칸). `balance`를 적어 두면 임포터가 시간순으로 잔액 흐름을 다시 계산해
한 글자라도 틀리면 파일을 거부하므로, 손으로 옮긴 내역도 믿고 쓸 수 있습니다. 형식 상세는
`backend/app/importers/manual_csv.py` 상단 주석 참고.

신한은행 PDF는 카드 내역과 겹치는 돈의 흐름을 이중 계산하지 않도록 처리합니다: 카드대금 결제(FB카드/FB자동/카드결제)와
본인 계좌 간 이체·예적금 해지·1원 인증·선불/지역화폐 충전(김포페이)은 `TRANSFER`로, 체크카드 출금은 신한카드 내역과 중복이므로 `is_excluded`로
저장되어 통계에서 빠집니다. 나머지 출금은 지출, 입금은 수입(`수입` 카테고리)으로 들어갑니다.

## 카테고리 분류 (Rule-based)

```bash
cd backend

# category_rules 시드 반영 (키워드 추가 후 재실행해도 안전)
./.venv/bin/python -m app.classifiers.seed_rules

# 아직 분류 안 된(미분류) 거래에 규칙 적용
./.venv/bin/python -m app.classifiers.reclassify run

# 수동으로 카테고리 교정 (해당 가맹점의 향후 거래에도 자동 반영됨)
./.venv/bin/python -m app.classifiers.reclassify correct <transaction_id> <category_id>
```

`app/classifiers/rules_data.py`에 `(카테고리 경로, 키워드, 우선순위)`를 추가하면 새 규칙이 늘어납니다.

## API 서버 실행

```bash
cd backend
./.venv/bin/uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs`에서 Swagger UI로 모든 엔드포인트를 확인/테스트할 수 있습니다.

주요 엔드포인트:

```text
GET   /transactions              (필터: start_date, end_date, category_id, card_id, merchant, q, currency 등)
GET   /transactions/summary      (목록과 같은 필터 → 지출/수입/이체 합계, 기간 전체 지출 대비 비중,
                                  선택 카테고리 한 단계 아래 기준의 비중 breakdown; currency 기본 KRW)
GET   /transactions/{id}
PATCH /transactions/{id}         (category_id/memo 수정 - category_id 지정 시 해당 가맹점 학습에도 반영)
GET   /categories                (트리 구조)

GET   /summary/monthly?year=&month=&currency=KRW
GET   /summary/category?year=&month=&currency=KRW
GET   /summary/merchant?year=&month=&currency=KRW&limit=
GET   /comparison/month?base_year=&base_month=&target_year=&target_month=
GET   /recurring-expenses?months=3&min_months_seen=2
GET   /budget?year=&month=
POST  /budget                    ({"year":,"month":,"amount":,"category_id":})
GET   /summary/trend?months=6    (최근 N개월 수입/지출 추이)
GET   /anomalies?year=&month=&lookback_months=3&min_change_pct=30  (평소 대비 급증/신규 지출 탐지)

GET   /cards                     (결제수단 목록)

GET    /category-rules
POST   /category-rules           ({"keyword":,"category_id":,"priority":,"match_type":,"enabled":})
PATCH  /category-rules/{id}
DELETE /category-rules/{id}

POST  /import                    (multipart 파일 업로드, ?preview=true 이면 DB에 반영하지 않고 미리보기만 계산)
```

모든 라우트는 `/api` 프리픽스가 붙습니다 (예: `/api/transactions`) - Dashboard가 `/api/*`만 백엔드로 프록시/서빙하기 때문입니다. `/health`만 예외로 루트에 있습니다.

**통화 처리**: KRW와 해외통화(USD 등)는 절대 합산하지 않습니다. `/summary/*`는 기본적으로 KRW만 집계하고,
`/summary/monthly` 응답의 `other_currencies` 필드로 KRW 외 통화 지출을 별도 표시합니다.

## Local Dashboard (React + Vite)

```bash
cd frontend
npm install

# 개발 모드 (HMR) - http://localhost:5173, /api/*는 Vite가 :8000으로 프록시
npm run dev

# 프로덕션 빌드 - dist/ 생성
npm run build
```

백엔드(`uvicorn app.main:app`)를 실행 중이면 `frontend/dist`가 존재하는 한 **백엔드 하나만 실행해도**
`http://localhost:8000`에서 Dashboard 전체가 그대로 서빙됩니다 (별도 프론트 서버 불필요).
`dist`가 없으면 `/`, `/transactions` 등은 그냥 API 404가 되므로, 개발 중에는 `npm run dev`로
:5173에 접속하세요.

화면: Dashboard(월별 요약/추이/카테고리별 지출/최근 거래), 거래내역(검색·필터·정렬·카테고리 수정 + 현재 필터의 합계/비중 패널),
카테고리(트리 + Rule 관리), 예산, 가져오기(파일 업로드 → 미리보기 → 실행).

계산은 전부 백엔드가 수행하고 Frontend는 결과를 시각화만 합니다 - 금액을 JS에서 재계산하지 않습니다.

## Local MCP Server (Claude 연동)

등록 (한 번만 실행하면 됨, user scope라 어느 디렉터리에서 Claude를 실행해도 사용 가능):

```bash
claude mcp add --scope user my-ledger -- \
  /Users/miguel/my-ledger/backend/.venv/bin/python \
  /Users/miguel/my-ledger/mcp-server/server.py
```

확인: `claude mcp list` 에 `my-ledger ... ✔ Connected`가 보이면 정상입니다.
해제하려면: `claude mcp remove my-ledger --scope user`

제공하는 Tool (모두 백엔드의 `stats_service`/`transaction_service`를 그대로 호출 - 임의 SQL 없음):

```text
get_monthly_summary(year, month, currency="KRW")
get_category_summary(year, month, currency="KRW")
get_merchant_summary(year, month, months=1, currency="KRW", limit=10)   # months>1이면 그 달까지 N개월 합산
compare_month(base_year, base_month, target_year, target_month, currency="KRW")
search_transactions(start_date, end_date, category, merchant, q, currency, limit=20)
get_recurring_expenses(months=3, min_months_seen=2, currency="KRW")
get_spending_anomalies(year, month, lookback_months=3, min_change_pct=30, currency="KRW")
get_budget_status(year, month, currency="KRW")
```

**AI 소비 분석 (Phase 9)은 API 키를 쓰지 않습니다.** Dashboard가 Anthropic API를 직접 호출하는 대신,
`/anomalies`로 계산된 사실(급증/신규 지출)만 화면에 보여주고, Dashboard의 "🤖 AI 소비 분석" 패널에서
추천 질문을 클릭하면 클립보드에 복사됩니다 - 그 질문을 이 MCP가 연결된 Claude 채팅에 붙여넣으면
Claude가 위 Tool들로 실제 데이터를 조회해 답합니다. 계산(증감률/평균/이상치 판정)은 전부
`stats_service.spending_anomalies()`가 수행하고, Claude는 그 결과를 해석/설명만 합니다.

수동으로 stdio 프로토콜 자체를 점검하려면 (실제 서버를 하위 프로세스로 띄워 tool을 호출):

```bash
cd mcp-server
../backend/.venv/bin/python smoke_test.py
```

MCP Tool은 카드/계좌번호를 절대 반환하지 않습니다 (DB에도 마스킹된 형태로만 저장되어 있음).

## DB 백업 / 복구

```bash
cd backend

# 백업: backups/ledger_YYYYMMDD_HHMMSS.db 생성
./.venv/bin/python -m app.core.backup_db backup

# 복구: 지정한 백업 파일로 data/ledger.db를 덮어씀
# (기존 DB는 data/ledger.db.before-restore로 안전하게 보관됨)
./.venv/bin/python -m app.core.backup_db restore ../backups/ledger_20260830_212354.db
```

## 프로젝트 구조

```text
my-ledger/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI 라우터 (Phase 5+)
│   │   ├── models/         # SQLAlchemy ORM 모델
│   │   ├── schemas/        # Pydantic 스키마 (Phase 5+)
│   │   ├── services/       # 통계/분류 비즈니스 로직 (Phase 4+)
│   │   ├── repositories/   # DB 접근 계층
│   │   ├── importers/      # 은행/카드사별 CSV Adapter (Phase 3)
│   │   ├── classifiers/    # Rule-based 카테고리 분류 (Phase 4)
│   │   └── core/           # 설정, DB 세션, 초기화/백업 스크립트
│   ├── alembic/            # DB 마이그레이션
│   └── tests/
├── mcp-server/              # Claude용 Local MCP Server (Phase 6)
├── frontend/                # React + TS + Vite Local Dashboard (Phase 8)
│   ├── src/
│   │   ├── api/             # fetch client, endpoint 함수, 타입
│   │   ├── components/      # 재사용 UI 컴포넌트
│   │   ├── pages/           # Dashboard/Transactions/Categories/Budget/Import
│   │   ├── hooks/           # useApiQuery 등
│   │   └── lib/             # 포맷팅 등 (계산 없음)
│   └── dist/                # npm run build 결과 (git 제외, 백엔드가 서빙)
├── data/ledger.db           # SQLite DB (git 제외)
├── imports/                 # 원본 CSV 보관 위치 (git 제외)
├── backups/                 # DB 백업 (git 제외)
└── .env                     # 로컬 환경 설정 (git 제외, .env.example 참고)
```

## 보안 원칙

- 카드/계좌번호는 마스킹된 형태로만 저장합니다 (예: `1234-****-****-5678`).
- 실제 CSV, DB 파일, `.env`는 Git에 commit하지 않습니다 (`.gitignore` 참고).
- MCP Tool은 임의 SQL을 실행하지 않고, 사전에 정의된 안전한 조회 Tool만 제공합니다.

## 구현 현황

- [x] Phase 1 — 설계 (Architecture / ERD / DB Schema / API / MCP Tool 목록)
- [x] Phase 2 — SQLite / SQLAlchemy / Alembic 셋업, 카테고리 시드, 백업/복구
- [x] Phase 3 — CSV/Excel Import (삼성/신한/현대카드 Adapter)
- [x] Phase 4 — Rule-based 카테고리 분류
- [x] Phase 5 — 통계 API (FastAPI)
- [x] Phase 6 — Local MCP Server (Claude Code 연동 완료)
- [ ] Phase 7 — 테스트
- [x] Phase 8 — Local Dashboard (React/Vite) - Dashboard, 거래내역, 카테고리/Rule, 예산, Import 화면 완료
- [x] Phase 9 — AI 소비 분석 (이상 지출 탐지 백엔드 + Dashboard 패널, API 키 없이 Claude 채팅으로 질의)
