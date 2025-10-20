#!/bin/sh
#
# Fix file permissions for OpenBSD deployment
# Run this script on the OpenBSD server as root
#

APP_DIR="/var/www/htdocs/www.chool.app"
APP_USER="www"
APP_GROUP="www"

echo "Fixing Charter Pool permissions for OpenBSD..."
echo "App directory: $APP_DIR"
echo "Owner: $APP_USER:$APP_GROUP"
echo ""

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    exit 1
fi

# Check if directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: App directory does not exist: $APP_DIR"
    exit 1
fi

cd "$APP_DIR" || exit 1

echo "Setting ownership..."
chown -R "$APP_USER:$APP_GROUP" .

echo "Setting directory permissions..."
find . -type d -not -path "./chool_env/*" -exec chmod 755 {} \;

echo "Setting file permissions..."
find . -type f -not -path "./chool_env/*" -exec chmod 644 {} \;

echo "Fixing venv permissions..."
chmod +x chool_env/bin/* 2>/dev/null || true

echo "Making scripts executable..."
chmod +x diagnose_openbsd.py 2>/dev/null || true
chmod +x test_fixes.py 2>/dev/null || true

echo "Checking critical files..."
for file in app.py auth.py models.py config.py secrets.txt VERSION; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (MISSING)"
    fi
done

echo "Checking critical directories..."
for dir in templates templates/admin static; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir"
    else
        echo "  ✗ $dir (MISSING)"
    fi
done

echo ""
echo "Permissions fixed!"
echo ""
echo "Now restart the service:"
echo "  rcctl restart gunicorn_chool"
echo ""
echo "To diagnose further issues, run:"
echo "  cd $APP_DIR && doas -u www ./chool_env/bin/python3 diagnose_openbsd.py"

