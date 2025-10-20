# Quick Fix for OpenBSD 500 Error

## 🚀 Fast Track (5 minutes)

### Step 1: Pull latest code
```bash
cd /var/www/htdocs/www.chool.app
doas -u www git pull
```

### Step 2: Fix permissions
```bash
doas sh fix_openbsd_permissions.sh
```

### Step 3: Restart
```bash
rcctl restart gunicorn_chool
```

### Step 4: Test
```bash
curl http://localhost:5150/health
```

**Expected output:**
```json
{"status": "ok", "database": "ok", "templates": "ok"}
```

## ✅ If it works now
You're done! The admin login should work.

## ❌ If still broken

### Quick Diagnostic:
```bash
cd /var/www/htdocs/www.chool.app
doas -u www ./chool_env/bin/python3 diagnose_openbsd.py
```

Look for red ✗ marks and fix those issues.

### Most Common Issues:

#### 1. Permission Denied on secrets.txt
```bash
doas chmod 644 secrets.txt
doas chown www:www secrets.txt
```

#### 2. Database Connection Failed
```bash
# Check PostgreSQL is running
rcctl check postgresql

# Test connection
doas -u www psql -U charter_pool -d charter_pool -c "SELECT 1;"
```

#### 3. Templates Not Found
```bash
doas chown -R www:www templates/
doas find templates/ -type d -exec chmod 755 {} \;
doas find templates/ -type f -exec chmod 644 {} \;
```

#### 4. Can't Read VERSION File
```bash
doas chmod 644 VERSION
doas chown www:www VERSION
```

### View Live Logs:
```bash
tail -f /var/log/messages | grep -E 'gunicorn|charter'
```

Look for:
- `[ERROR]` - Something is broken
- `[WARNING]` - Something is misconfigured but working
- `[INFO]` - Normal startup messages

### Run in Foreground (See Errors Directly):
```bash
rcctl stop gunicorn_chool
cd /var/www/htdocs/www.chool.app
doas -u www ./chool_env/bin/gunicorn --bind 127.0.0.1:5150 app:app
```

Press Ctrl+C to stop, then:
```bash
rcctl start gunicorn_chool
```

## 📚 Need More Help?
See `OPENBSD_DEBUGGING.md` for complete troubleshooting guide.

## 🔍 Key Changes Made:
- Added error handling to prevent crashes
- Added /health endpoint for monitoring  
- Added diagnostic tools
- Added comprehensive logging
- Fixed permission-related issues

All changes are backwards compatible and work on both local dev and OpenBSD production.

