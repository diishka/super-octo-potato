#!/usr/bin/env sh

set -eu

echo "Waiting for PostgreSQL for showcase refresher..."
python - <<'PY'
import os
import time
import psycopg2

dbname = os.getenv("POSTGRES_DB", "social_movies")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
host = os.getenv("POSTGRES_HOST", "postgres")
port = os.getenv("POSTGRES_PORT", "5432")

for attempt in range(30):
    try:
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        connection.close()
        print("PostgreSQL is ready for showcase refresher.")
        break
    except Exception as exc:
        if attempt == 29:
            raise
        print(f"PostgreSQL is unavailable ({exc}), retrying...")
        time.sleep(2)
PY

sleep "${SHOWCASE_REFRESH_START_DELAY:-15}"

while true; do
  echo "Running daily showcase refresh..."
  python manage.py refresh_movie_showcase || true
  sleep "${SHOWCASE_REFRESH_INTERVAL_SECONDS:-86400}"
done
