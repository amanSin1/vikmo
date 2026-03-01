#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn vikmo_backend.wsgi:application --bind 0.0.0.0:$PORT