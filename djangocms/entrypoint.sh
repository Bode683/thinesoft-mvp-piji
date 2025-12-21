#!/bin/sh

set -e

echo "Starting Django in $DJANGO_ENV mode..."


if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    # Wait for the PostgreSQL server to be available
    until PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$DJANGO_DB_HOST" -U "$DJANGO_DB_USER" -d "postgres" -c '\q'; do
      >&2 echo "Postgres server is unavailable - sleeping"
      sleep 1
    done

    >&2 echo "Postgres server is up - continuing..."

    # Check if the database exists, and create it if it doesn't.
    # We connect to the default 'postgres' database to run this check.
    PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$DJANGO_DB_HOST" -U "$DJANGO_DB_USER" -d "postgres" -tc "SELECT 1 FROM pg_database WHERE datname = '$DJANGO_DB_NAME'" | grep -q 1 || \
    PGPASSWORD=$DJANGO_DB_PASSWORD psql -h "$DJANGO_DB_HOST" -U "$DJANGO_DB_USER" -d "postgres" -c "CREATE DATABASE \"$DJANGO_DB_NAME\""

    echo "PostgreSQL started"
fi

# Wait for DB to be ready before running migrations
# python manage.py wait_for_db

# Apply migrations
python manage.py migrate --noinput

# Create superuser if not exists

echo "Creating superuser if not exists..."

python manage.py shell << END
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME')
email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

if username and email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"Superuser {username} created.")
    else:
        print(f"Superuser {username} already exists.")
else:
    print("Superuser env vars not set, skipping creation.")
END

if [ "$DJANGO_ENV" = "production" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    echo "Starting Gunicorn..."
    exec gunicorn djangocms.wsgi:application --bind 0.0.0.0:8000

else
    echo "Starting development server..."
    exec python manage.py runserver 0.0.0.0:8000
fi

exec "$@"