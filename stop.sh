#!/bin/bash
# my-ledger 종료 스크립트 - start.sh 로 띄운 백엔드(uvicorn)를 종료하고 포트가 풀릴 때까지 대기
ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$ROOT/.run/uvicorn.pid"
PORT=8000

targets=""

# 1) PID 파일에 기록된 프로세스와 그 자식
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE")"
  if kill -0 "$PID" 2>/dev/null; then
    targets="$targets $PID $(pgrep -P "$PID" 2>/dev/null | tr '\n' ' ')"
  fi
  rm -f "$PID_FILE"
fi

# 2) 포트를 점유한 uvicorn (PID 파일이 없거나 stale인 경우 대비)
for p in $(lsof -nP -tiTCP:$PORT -sTCP:LISTEN 2>/dev/null); do
  if ps -o command= -p "$p" | grep -q "uvicorn app.main:app"; then
    targets="$targets $p"
  fi
done

targets="$(echo $targets | tr ' ' '\n' | sort -u | tr '\n' ' ')"
if [ -z "$targets" ]; then
  echo "실행 중인 my-ledger 백엔드가 없습니다."
  exit 0
fi

kill $targets 2>/dev/null
echo "백엔드 종료 요청 (PID:$targets)"

# 3) 종료 및 포트 해제 대기 (최대 10초, 이후 강제 종료)
for i in $(seq 1 20); do
  alive=0
  for p in $targets; do kill -0 "$p" 2>/dev/null && alive=1; done
  if [ "$alive" -eq 0 ] && ! lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    echo "✔ 종료 완료"
    exit 0
  fi
  sleep 0.5
done

echo "정상 종료되지 않아 강제 종료합니다."
kill -9 $targets 2>/dev/null
sleep 0.5
echo "✔ 종료 완료"
