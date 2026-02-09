#!/bin/bash

# Exit on error
set -e

echo "🔍 Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "✅ PostgreSQL started"

echo "🔍 Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.5
done
echo "✅ Redis started"

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info