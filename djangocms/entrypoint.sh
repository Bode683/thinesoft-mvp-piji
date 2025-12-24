#!/bin/sh

set -e

echo "Starting Django in $DJANGO_ENV mode..."

# Read secrets and export as environment variables
if [ -f /run/secrets/djangocms_db_password ]; then
  export SQL_PASSWORD=$(cat /run/secrets/djangocms_db_password)
  echo "✓ Django DB password loaded from secret"
else
  echo "⚠ Warning: djangocms_db_password secret not found"
fi

if [ -f /run/secrets/django_secret_key ]; then
  export SECRET_KEY=$(cat /run/secrets/django_secret_key)
  echo "✓ Django SECRET_KEY loaded from secret"
else
  echo "⚠ Warning: django_secret_key secret not found"
fi

if [ -f /run/secrets/django_superuser_password ]; then
  export DJANGO_SUPERUSER_PASSWORD=$(cat /run/secrets/django_superuser_password)
  echo "✓ Django superuser password loaded from secret"
else
  echo "⚠ Warning: django_superuser_password secret not found"
fi

if [ -f /run/secrets/djangocms_keycloak_client_secret ]; then
  export KEYCLOAK_CLIENT_SECRET=$(cat /run/secrets/djangocms_keycloak_client_secret)
  echo "✓ Keycloak client secret loaded from secret"
else
  echo "⚠ Warning: djangocms_keycloak_client_secret secret not found"
fi


if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    # Wait for the PostgreSQL server to be available
    until PGPASSWORD=$SQL_PASSWORD psql -h "$SQL_HOST" -U "$SQL_USER" -d "postgres" -c '\q'; do
      >&2 echo "Postgres server is unavailable - sleeping"
      sleep 1
    done

    >&2 echo "Postgres server is up - continuing..."

    # Check if the database exists, and create it if it doesn't.
    # We connect to the default 'postgres' database to run this check.
    # NOTE: Database creation is handled by init script, so this is just a fallback
    PGPASSWORD=$SQL_PASSWORD psql -h "$SQL_HOST" -U "$SQL_USER" -d "postgres" -tc "SELECT 1 FROM pg_database WHERE datname = '$SQL_DATABASE'" | grep -q 1 || \
    PGPASSWORD=$SQL_PASSWORD psql -h "$SQL_HOST" -U "$SQL_USER" -d "postgres" -c "CREATE DATABASE \"$SQL_DATABASE\""

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
    exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000

else
    echo "Starting development server..."
    exec python manage.py runserver 0.0.0.0:8000
fi

exec "$@"