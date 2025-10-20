# OpenBSD Deployment Debugging Guide

## Issue: 500 Internal Server Error on Admin Login

When you see a 500 error and the backend doesn't even log the GET request, it means the error is happening before Flask processes the request. Common causes on OpenBSD:

### 1. File Permission Issues

The `www` user must be able to read all application files.

**Fix:**
```bash
doas sh fix_openbsd_permissions.sh
```

Or manually:
```bash
cd /var/www/htdocs/www.chool.app
doas chown -R www:www .
doas find . -type d -exec chmod 755 {} \;
doas find . -type f -exec chmod 644 {} \;
```

**Verify:**
```bash
cd /var/www/htdocs/www.chool.app
doas -u www ls -la
doas -u www cat secrets.txt
doas -u www cat VERSION
```

### 2. Database Connection Issues

PostgreSQL socket permissions or connection strings might be wrong.

**Check:**
```bash
# Check if PostgreSQL is running
rcctl check postgresql

# Check database connection as www user
doas -u www psql -U charter_pool -d charter_pool -c "SELECT 1;"
```

**Common fixes:**
- Verify `DATABASE_URL` in environment or config
- Check PostgreSQL `pg_hba.conf` for authentication settings
- Ensure PostgreSQL socket has correct permissions (`/tmp/.s.PGSQL.5432`)

### 3. Missing Dependencies

**Verify all Python packages are installed:**
```bash
cd /var/www/htdocs/www.chool.app
doas -u www ./chool_env/bin/pip list
```

Required packages:
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Flask-Talisman
- psycopg2-binary
- gunicorn
- werkzeug

### 4. Template/Static File Issues

**Verify templates are readable:**
```bash
cd /var/www/htdocs/www.chool.app
doas -u www ls -la templates/
doas -u www ls -la templates/admin/
doas -u www cat templates/admin/login.html
```

### 5. Run Diagnostic Script

The diagnostic script will check all common issues:

```bash
cd /var/www/htdocs/www.chool.app
doas -u www ./chool_env/bin/python3 diagnose_openbsd.py
```

This will check:
- File permissions
- Directory permissions  
- Database connectivity
- Template loading
- Python imports
- Configuration loading

### 6. Check Gunicorn Logs

```bash
# Check if gunicorn is running
rcctl check gunicorn_chool

# View logs (if logging to syslog)
tail -f /var/log/messages | grep gunicorn

# Or check gunicorn error output
ps aux | grep gunicorn
```

### 7. Test Health Endpoint

After deploying the fixes, test the health endpoint:

```bash
curl http://localhost:5150/health
```

Should return JSON with status of database and templates.

### 8. View Detailed Logs

The application now has extensive debug logging. To see them:

```bash
# If using syslog
tail -f /var/log/messages | grep -E '\[INFO\]|\[DEBUG\]|\[ERROR\]|\[WARNING\]'

# If gunicorn is logging to a file
tail -f /path/to/gunicorn.log
```

Look for:
- `[INFO] Flask app initialized`
- `[INFO] Database connection successful` 
- `[ERROR] Database connection failed`
- `[WARNING] Could not read VERSION file`
- `[ERROR] Failed to load user from session`

### 9. Manual Test

Try running the app directly as the www user:

```bash
cd /var/www/htdocs/www.chool.app
doas -u www ./chool_env/bin/python3 -c "from app import app; print('Import successful')"
```

If this fails, you'll see the actual error message.

### 10. Restart Service

After making changes:

```bash
rcctl restart gunicorn_chool
rcctl check gunicorn_chool
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| `Permission denied` reading secrets.txt | `chmod 644 secrets.txt && chown www:www secrets.txt` |
| `No such file or directory` for templates | Check template_folder path, ensure templates/ exists |
| Database connection timeout | Check PostgreSQL is running, verify DATABASE_URL |
| Import errors | Activate venv and install requirements: `pip install -r requirements.txt` |
| Session issues | Verify SECRET_KEY is set correctly |

### Emergency Fallback

If templates are completely broken, the app will render a plain HTML 500 page. Check logs to see the actual error.

### Still Not Working?

1. Check file ownership: `ls -la /var/www/htdocs/www.chool.app/`
2. Check process user: `ps aux | grep gunicorn`
3. Check database: `psql -U charter_pool -d charter_pool -c "\dt"`
4. Check Python path: `doas -u www ./chool_env/bin/python3 -c "import sys; print(sys.path)"`
5. Try running in foreground: `doas -u www ./chool_env/bin/gunicorn --bind 127.0.0.1:5150 app:app`

The last command will show errors directly in the terminal.

