#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================="
echo "  Bako Bakery — starting backend + frontend"
echo "============================================="

# Seed database and train prediction model
echo "  Seeding database…"
uv run python src/test/seed_fake_data.py --reset
echo "  Training prediction model…"
uv run python -m src.prediction_model
echo

# Start backend
uv run -m src &
BACKEND_PID=$!
echo "  Backend  →  http://localhost:8000  (pid $BACKEND_PID)"

# Give uvicorn a moment to bind
sleep 2

# Start frontend
cd "$ROOT/FRONTEND"
if [ ! -d "node_modules" ]; then
  echo "  Installing frontend dependencies…"
  npm install
fi
npm run dev &
FRONTEND_PID=$!
echo "  Frontend →  http://localhost:5173  (pid $FRONTEND_PID)"

# Start tablet app
cd "$ROOT/src/app"
uv run uvicorn main:app --port 8080 --reload &
TABLET_PID=$!

echo "  Tablet App →  http://localhost:8080  (pid $TABLET_PID)"
echo
echo "Press Ctrl+C to stop both servers."
echo

# Stop both on Ctrl+C
trap "echo; echo 'Shutting down…'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; wait; echo 'Done.'" INT TERM

wait
