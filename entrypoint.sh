#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Create superuser if not exists
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@vikmo.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

gunicorn vikmo_backend.wsgi:application --bind 0.0.0.0:$PORT