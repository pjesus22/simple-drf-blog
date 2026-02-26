#!/bin/sh
set -e

python src/manage.py migrate --noinput

# Only collect static files for the web server, not the task worker
if [ "$1" = "gunicorn" ]; then
    python src/manage.py collectstatic --noinput
fi

exec "$@"
