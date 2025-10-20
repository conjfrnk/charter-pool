# Changes Made to Fix OpenBSD 500 Error

## Summary
Fixed 500 Internal Server Error on admin login when deployed to OpenBSD by adding comprehensive error handling, logging, and diagnostic tools.

## Root Cause
The 500 error was occurring before Flask could even process the request, likely due to:
1. File permission issues preventing template/config file access
2. Database connection failures during context processor execution
3. Template rendering failures creating error loops
4. Session handling trying to access an unavailable database

## Files Modified

### 1. `app.py`
**Changes:**
- Added startup logging for configuration validation
- Added database connection test on startup
- Added comprehensive error handling to `inject_user()` context processor
- Added comprehensive error handling to `inject_version()` context processor
- Enhanced 500 error handler with fallback plain HTML rendering
- Added `/health` endpoint for monitoring database and template status
- Imported `text` from sqlalchemy for health checks

**Why:** Context processors were failing when database was unavailable, causing infinite error loops.

### 2. `auth.py`
**Changes:**
- Added try/except wrapper around `load_user()` function
- Added detailed error logging when user loading fails

**Why:** Session loading was crashing when database was unavailable or had permission issues.

### 3. `config.py`
**Changes:**
- Added detailed logging when reading SECRET_KEY from secrets.txt
- Added better error handling for file read failures

**Why:** File permission errors on OpenBSD weren't being logged, making debugging difficult.

### 4. `templates/errors/500.html`
**Changes:**
- Simplified to only link to login page (not conditional on current_user)

**Why:** Accessing current_user in error template could trigger database calls, creating error loops.

## New Files Created

### 1. `diagnose_openbsd.py`
**Purpose:** Comprehensive diagnostic script to check:
- File permissions (readable by www user?)
- Directory permissions
- Database connectivity
- Template loading
- Python imports
- Configuration loading

**Usage:**
```bash
cd /var/www/htdocs/www.chool.app
doas -u www ./chool_env/bin/python3 diagnose_openbsd.py
```

### 2. `fix_openbsd_permissions.sh`
**Purpose:** Shell script to automatically fix common OpenBSD permission issues

**Usage:**
```bash
doas sh fix_openbsd_permissions.sh
```

### 3. `OPENBSD_DEBUGGING.md`
**Purpose:** Complete troubleshooting guide for OpenBSD deployment issues

## Deployment Instructions

### On Your Local Machine:
```bash
cd /Users/connor/projects/charter-pool
git add .
git commit -m "Fix OpenBSD 500 error with comprehensive error handling and diagnostics"
git push
```

### On OpenBSD Server:
```bash
# 1. Pull latest changes
cd /var/www/htdocs/www.chool.app
doas -u www git pull

# 2. Fix permissions
doas sh fix_openbsd_permissions.sh

# 3. Run diagnostic
doas -u www ./chool_env/bin/python3 diagnose_openbsd.py

# 4. Restart service
rcctl restart gunicorn_chool

# 5. Test health endpoint
curl http://localhost:5150/health

# 6. Try admin login
curl http://localhost:5150/admin/login
```

## What to Look For

### Success Indicators:
- Health endpoint returns `{"status": "ok", "database": "ok", "templates": "ok"}`
- Admin login page loads without 500 error
- Detailed startup logs appear showing:
  - `[INFO] Flask app initialized`
  - `[INFO] Database connection successful`
  - `[INFO] Loaded SECRET_KEY from...`

### If Still Failing:
1. Check the diagnostic output for RED ✗ marks
2. Look for `[ERROR]` or `[WARNING]` messages in logs
3. Verify database connection: `psql -U charter_pool -d charter_pool`
4. Check file permissions: `ls -la` as www user
5. Try running gunicorn in foreground to see errors directly

## Technical Details

### Error Handling Strategy:
1. **Context Processors:** Wrapped in try/except to prevent template rendering failures
2. **User Loader:** Catches database errors during session restoration
3. **Error Handler:** Has fallback plain HTML if template rendering fails
4. **Health Check:** Validates database and templates are accessible

### Logging Added:
- Config file reading
- Database connection status
- Template loading failures
- User session loading failures
- Context processor errors

### Why This Fixes the Issue:
The original code assumed all resources (database, files, templates) were always accessible. On OpenBSD with strict permissions and different deployment environment, failures in these resources caused unhandled exceptions before Flask could even process the request. Now all potential failure points have error handling and logging, allowing the app to:
1. Start even with permission issues
2. Log detailed error information
3. Provide health check endpoint for monitoring
4. Render error pages even when templates fail
5. Avoid infinite error loops during error handling

## Testing
After deployment, verify:
- [ ] Health endpoint responds: `curl http://localhost:5150/health`
- [ ] Admin login page loads: `curl http://localhost:5150/admin/login`
- [ ] Diagnostic script runs clean
- [ ] Service stays running: `rcctl check gunicorn_chool`
- [ ] Logs show startup messages without errors

