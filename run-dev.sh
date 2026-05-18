#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"

backend_pid=""
frontend_pid=""

cleanup() {
  local exit_code=$?

  if [[ -n "${frontend_pid}" ]] && kill -0 "${frontend_pid}" 2>/dev/null; then
    kill "${frontend_pid}" 2>/dev/null || true
  fi

  if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
    kill "${backend_pid}" 2>/dev/null || true
  fi

  wait "${frontend_pid}" 2>/dev/null || true
  wait "${backend_pid}" 2>/dev/null || true

  exit "${exit_code}"
}

trap cleanup INT TERM EXIT

if [[ ! -x "$BACKEND_PYTHON" ]]; then
  echo "Backend venv not found: $BACKEND_PYTHON"
  echo "Create it first:"
  echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is not installed. Install Node.js/npm first."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "frontend/node_modules not found."
  echo "Run first:"
  echo "  cd frontend && npm install"
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  echo "Starting PostgreSQL container..."
  if ! (cd "$ROOT_DIR" && docker compose up -d postgres); then
    echo "Warning: could not start postgres via docker compose."
    echo "If PostgreSQL is already running separately, you can ignore this message."
  fi
else
  echo "docker not found, skipping PostgreSQL startup."
fi

echo "Starting Django backend on http://127.0.0.1:8000 ..."
(
  cd "$BACKEND_DIR"
  exec "$BACKEND_PYTHON" manage.py runserver 0.0.0.0:8000
) &
backend_pid=$!

echo "Starting Vite frontend on http://127.0.0.1:5173 ..."
(
  cd "$FRONTEND_DIR"
  exec npm run dev
) &
frontend_pid=$!

echo "Dev stack is starting."
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:5173"
echo "Press Ctrl+C to stop both."

wait -n "$backend_pid" "$frontend_pid"
