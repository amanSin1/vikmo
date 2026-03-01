#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
<<<<<<< HEAD
gunicorn vikmo_backend.wsgi:application --bind 0.0.0.0:$PORT
=======
gunicorn vikmo_backend.wsgi:application --bind 0.0.0.0:$PORT
>>>>>>> 74c5ebaef138252fd513265ab70562882ff5829c
