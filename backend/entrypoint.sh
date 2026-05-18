#!/usr/bin/env sh

set -eu

echo "Waiting for PostgreSQL..."
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
        print("PostgreSQL is ready.")
        break
    except Exception as exc:
        if attempt == 29:
            raise
        print(f"PostgreSQL is unavailable ({exc}), retrying...")
        time.sleep(2)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile -
