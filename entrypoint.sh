#!/bin/sh
set -e

# Only clear and collect static files if this container is running migrations
if [ "$COLLECT_STATIC" = "1" ]; then
    echo "Clearing and collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

exec "$@"
