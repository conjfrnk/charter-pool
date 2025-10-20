#!/bin/sh
# Helper script to view Charter Pool application logs

echo "=== Charter Pool Log Viewer ==="
echo ""

# Check if running as daemon
if rcctl check gunicorn_chool > /dev/null 2>&1; then
    echo "✓ gunicorn_chool service is running"
    echo ""
fi

# Common log locations on OpenBSD
LOG_LOCATIONS="/var/log/daemon /var/log/messages /var/log/gunicorn_chool.log /var/www/logs/gunicorn.log /tmp/gunicorn.log"

echo "Searching for logs in common locations..."
for log in $LOG_LOCATIONS; do
    if [ -f "$log" ]; then
        echo "Found: $log"
    fi
done

echo ""
echo "=== Tailing gunicorn output (last 100 lines) ==="
echo ""

# Try to find and tail the log
if [ -f "/var/log/daemon" ]; then
    tail -100 /var/log/daemon | grep -i "charter\|gunicorn\|DEBUG\|ERROR" || echo "No charter-pool related logs found"
elif [ -f "/var/log/messages" ]; then
    tail -100 /var/log/messages | grep -i "charter\|gunicorn\|DEBUG\|ERROR" || echo "No charter-pool related logs found"
else
    echo "Could not find standard log files"
    echo ""
    echo "Try checking rcctl output:"
    echo "  rcctl check gunicorn_chool"
    echo "  rcctl restart gunicorn_chool"
fi

echo ""
echo "=== To watch logs in real-time ==="
echo "Run one of these commands:"
echo "  tail -f /var/log/daemon | grep -i charter"
echo "  tail -f /var/log/messages | grep -i charter"
echo ""
echo "=== After restarting, try to add users and watch for DEBUG output ==="

