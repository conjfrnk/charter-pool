#!/bin/sh
# Force reload all Python code and restart

echo "=== Force Reload Charter Pool ==="
echo ""

cd /var/www/htdocs/www.chool.app

echo "[1/4] Removing Python cache files..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "✓ Cache cleared"

echo ""
echo "[2/4] Checking file permissions..."
ls -la app.py auth.py models.py | head -5

echo ""
echo "[3/4] Stopping gunicorn..."
doas rcctl stop gunicorn_chool
sleep 2

echo ""
echo "[4/4] Starting gunicorn..."
doas rcctl start gunicorn_chool
sleep 2

echo ""
echo "=== Status Check ==="
rcctl check gunicorn_chool
if [ $? -eq 0 ]; then
    echo "✓ gunicorn_chool is running"
    echo ""
    echo "Try adding users now. If it still fails:"
    echo "1. Check the error message (should show detailed error now)"
    echo "2. Run: tail -f /var/log/daemon | grep -E 'DEBUG|ERROR'"
else
    echo "✗ gunicorn_chool failed to start"
    echo "Check logs: tail -50 /var/log/daemon"
fi

