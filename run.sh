#!/usr/bin/env bash
set -e
# uv run python  src/test/test_voice.py --use-real-db
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================="
echo "  Bako Bakery — starting backend + frontend"
echo "============================================="

# Start backend
uv run -m src &
BACKEND_PID=$!
echo "  Backend  →  http://localhost:8000  (pid $BACKEND_PID)"

# Give uvicorn a moment to bind
sleep 2

# Start frontend
cd "$ROOT/FRONTEND"
npm run dev &
FRONTEND_PID=$!
echo "  Frontend →  http://localhost:5173  (pid $FRONTEND_PID)"
echo
echo "Press Ctrl+C to stop both servers."
echo

# Stop both on Ctrl+C
trap "echo; echo 'Shutting down…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; wait; echo 'Done.'" INT TERM

wait
