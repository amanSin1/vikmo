#!/bin/bash

echo "Waiting for PostgreSQL to be ready..."

while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    echo "PostgreSQL is unavailable - sleeping..."
    sleep 2
done

echo "PostgreSQL is up - running migrations..."
python manage.py migrate

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000