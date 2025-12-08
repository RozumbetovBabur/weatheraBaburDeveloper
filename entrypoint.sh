#!/usr/bin/env bash
set -e

# echo "Waiting for DB..."
# sleep 2

# Apply migrations (ignore failures for dev)
python manage.py migrate --noinput || true

# python manage.py collectstatic --noinput || true

# Agar CMD argumentleri berilgen bolsa, exec etin'
if [ $# -gt 0 ]; then
  exec "$@"
else
  # default: start django server (dev only)
  exec python manage.py runserver 0.0.0.0:8000
fi
