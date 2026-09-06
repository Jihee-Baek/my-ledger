#!/bin/bash
# my-ledger 시작 스크립트
#  - 최초 실행 시 venv / node_modules 자동 설치
#  - DB 마이그레이션 적용
#  - 프론트엔드 빌드(소스가 dist보다 새로울 때만)
#  - 백엔드(uvicorn)를 백그라운드로 띄우고 브라우저를 엶
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
PY="$BACKEND/.venv/bin/python"
RUN_DIR="$ROOT/.run"
PID_FILE="$RUN_DIR/uvicorn.pid"
LOG_FILE="$RUN_DIR/uvicorn.log"
HOST=127.0.0.1
PORT=8000

mkdir -p "$RUN_DIR"

# 이미 실행 중이면 브라우저만 연다
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "이미 실행 중입니다 (PID $(cat "$PID_FILE")). http://$HOST:$PORT"
  open "http://$HOST:$PORT"
  exit 0
fi
if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  echo "포트 $PORT 를 다른 프로세스가 사용 중입니다. 먼저 ./stop.sh 를 실행하세요."
  lsof -nP -iTCP:$PORT -sTCP:LISTEN
  exit 1
fi

# 1) Python venv
if [ ! -x "$PY" ]; then
  echo "▶ Python venv 생성 및 의존성 설치"
  python3.12 -m venv "$BACKEND/.venv"
  "$BACKEND/.venv/bin/pip" install -q -r "$BACKEND/requirements.txt"
fi

# 2) DB 마이그레이션
echo "▶ DB 마이그레이션 적용"
(cd "$BACKEND" && ./.venv/bin/alembic upgrade head >"$LOG_FILE" 2>&1 || { echo "✖ 마이그레이션 실패"; cat "$LOG_FILE"; exit 1; })

# 3) 프론트엔드 빌드 (dist가 없거나 src가 더 새로울 때만)
if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "▶ npm install"
  (cd "$FRONTEND" && npm install --silent)
fi
if [ ! -f "$FRONTEND/dist/index.html" ] || [ -n "$(find "$FRONTEND/src" "$FRONTEND/index.html" "$FRONTEND/package.json" -newer "$FRONTEND/dist/index.html" 2>/dev/null | head -1)" ]; then
  echo "▶ 프론트엔드 빌드"
  (cd "$FRONTEND" && npm run build --silent >/dev/null)
fi

# 4) 백엔드 실행
echo "▶ 백엔드 실행 (http://$HOST:$PORT)"
(cd "$BACKEND" && nohup ./.venv/bin/uvicorn app.main:app --host $HOST --port $PORT </dev/null >"$LOG_FILE" 2>&1 & echo $! >"$PID_FILE")

for _ in $(seq 1 20); do
  if curl -sf "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    echo "✔ 실행 완료 (PID $(cat "$PID_FILE")) - 로그: $LOG_FILE"
    open "http://$HOST:$PORT"
    exit 0
  fi
  sleep 0.5
done

echo "✖ 서버가 응답하지 않습니다. 로그를 확인하세요: $LOG_FILE"
tail -20 "$LOG_FILE"
exit 1
