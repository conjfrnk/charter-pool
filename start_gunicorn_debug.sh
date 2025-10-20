#!/bin/sh
# Start gunicorn manually to see the error

echo "=== Starting Gunicorn in DEBUG mode ==="
echo "This will show the actual error preventing startup"
echo ""

cd /var/www/htdocs/www.chool.app

echo "Running as www user..."
doas -u www /var/www/htdocs/www.chool.app/chool_env/bin/gunicorn \
    --chdir /var/www/htdocs/www.chool.app \
    --bind 127.0.0.1:5150 \
    --workers 1 \
    --timeout 60 \
    --env PGUSER=charter_pool \
    app:app

# This will run in foreground and show errors
# Press Ctrl+C to stop

