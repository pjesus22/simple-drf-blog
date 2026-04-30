#!/bin/sh
set -e

# Only collect static files for the web server, not the task worker
if [ "$1" = "gunicorn" ]; then
    python src/manage.py collectstatic --noinput
fi

exec "$@"
