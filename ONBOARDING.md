# Onboarding Guide

Quick-start guide for developers and AI agents working on Charter Pool.

## Quick Start (5 minutes)

```bash
# 1. Setup environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Create secret key (min 32 chars)
python3 -c "import secrets; print(secrets.token_urlsafe(32))" > secrets.txt

# 3. Setup PostgreSQL database
createdb charter_pool
# Or connect to existing: export DATABASE_URL=postgresql://user@host/charter_pool

# 4. Initialize database and run
python3 init_db.py
python3 app.py
```

Default admin: `admin` / `admin` (change immediately at `/admin/login`)

## Project Overview

**Charter Pool** is a Flask web app for tracking pool (billiards) games and ELO rankings at Princeton Charter Club.

| Layer | Technology |
|-------|------------|
| Backend | Python 3.7+, Flask 2.x |
| Database | PostgreSQL 12+ (SQLAlchemy ORM) |
| Cache/Rate Limiting | Flask-Caching (SimpleCache) + Flask-Limiter |
| Frontend | Jinja2, Vanilla JS, CSS3 |
| Production | Gunicorn (OpenBSD with rc.d scripts) |

## File Structure

```
charter-pool/
├── app.py              # Entry point, routes, error handlers, middleware
├── config.py           # Configuration (secret key, DB, cache, ELO settings)
├── models.py           # SQLAlchemy models (User, Admin, Game, Tournament)
├── auth.py             # Authentication (login, sessions, user creation)
├── elo.py              # ELO rating calculations (singles and doubles)
├── tournament_logic.py # Tournament bracket generation and management
├── cache_utils.py      # Cache management and invalidation
├── performance.py      # Performance monitoring utilities
├── init_db.py          # Database initialization script
├── gunicorn.conf.py    # Production Gunicorn configuration
├── static/             # main.js, style.css, pcc_logo.png
├── templates/          # Jinja2 templates
│   ├── layout.html     # Base template
│   ├── index.html      # User dashboard
│   ├── login.html      # User login
│   ├── report_game.html # Game reporting form
│   ├── leaderboard.html # ELO rankings
│   ├── tournaments.html # Tournament list
│   ├── admin/          # Admin templates
│   └── errors/         # Error pages (400, 403, 404, 500)
├── rc.d/               # OpenBSD init scripts (gunicorn_chool)
├── secrets.txt         # Secret key (gitignored)
├── VERSION             # Version for cache busting
└── archive/            # Migration scripts, old docs
```

## Key Patterns

### Route Pattern
```python
@app.route("/path", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # sensitive routes
@login_required
def route_name():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    user = get_current_user()
    
    if request.method == "POST":
        value = request.form.get("field", "").strip().lower()
        if not value:
            flash("Field required.", "error")
            return redirect(url_for('route_name'))
        try:
            # Database operations
            db.session.commit()
            flash("Success.", "success")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error: {e}")
            flash("An error occurred.", "error")
        return redirect(url_for('route_name'))
    return render_template("template.html", user=user)
```

### Database Access (SQLAlchemy ORM)
```python
# Query single user
user = User.query.get(netid)

# Query with filters
active_users = User.query.filter_by(archived=False, is_active=True).all()

# Complex queries with eager loading
games = Game.query.options(
    joinedload(Game.player1),
    joinedload(Game.player2)
).filter(Game.player1_netid == netid).all()

# Commit changes
db.session.add(new_object)
db.session.commit()
```

### Input Validation
```python
netid = request.form.get("netid", "").strip().lower()
if not netid or len(netid) > 50:
    flash("Invalid NetID.", "error")
    return redirect(url_for('route'))
```

### Caching
```python
# Get from cache or compute
cache_key = 'leaderboard:top10'
leaderboard = cache.get(cache_key)
if leaderboard is None:
    leaderboard = User.query.filter_by(archived=False).order_by(desc(User.elo_rating)).limit(10).all()
    cache.set(cache_key, leaderboard, timeout=60)

# Invalidate after data changes
invalidate_game_caches(cache_manager)
```

## Security Checklist

| Requirement | Implementation |
|-------------|----------------|
| CSRF | Flask-WTF CSRFProtect enabled globally |
| SQL Injection | SQLAlchemy ORM (parameterized by default) |
| Passwords | `generate_password_hash(pw, method="pbkdf2:sha256")` |
| Sessions | 1-year lifetime, Secure/HTTPOnly/SameSite=Lax |
| Rate Limiting | `@limiter.limit("5/minute")` on admin login |
| Input | Strip, lowercase NetIDs, validate lengths |
| CSP | Flask-Talisman with strict policy |
| HTTPS | Configurable via `FORCE_HTTPS` env var |

## Database Schema (Core Tables)

| Table | Purpose |
|-------|---------|
| `users` | netid (PK), first_name, last_name, elo_rating, is_active, archived |
| `admins` | id, username, password_hash |
| `games` | id, game_type, player1-4_netid, winner_netid, elo_change, timestamp |
| `tournaments` | id, name, format, status, created_by_admin_id |
| `tournament_participants` | id, tournament_id, user_netid, self_rating, seed |
| `tournament_matches` | id, tournament_id, round_number, player1/2_netid, winner_netid |

### Key Relationships
- Users can be player1, player2, player3, or player4 in games
- Singles games: player1 vs player2
- Doubles games: (player1, player2) vs (player3, player4)
- Tournament matches link to games when completed

## ELO System

- Default rating: 1200
- K-factor: 32
- Singles: Standard ELO calculation
- Doubles: Uses team average rating for calculation

```python
# Singles
elo_change = update_ratings_after_game(winner, loser, k_factor=32)

# Doubles
elo_change = update_ratings_after_doubles_game(
    team1_players=[user, partner],
    team2_players=[opponent1, opponent2],
    winning_team=1,  # or 2
    k_factor=32
)
```

## CLI Commands

```bash
# Initialize database with default admin
python3 init_db.py

# Run development server
python3 app.py

# Run with Gunicorn (production)
gunicorn -c gunicorn.conf.py app:app
```

## Common Tasks

### Add a new route
1. Add route function in `app.py` (user routes) or appropriate section
2. Use `@login_required` decorator
3. Check `current_user.is_admin` if route is user-only
4. Add rate limiting for sensitive endpoints
5. Create template in `templates/`

### Modify database schema
1. Update models in `models.py`
2. Create migration script in `archive/` (e.g., `migrate_add_field.py`)
3. Run migration: `python3 archive/migrate_add_field.py`
4. Alternatively, drop and recreate for dev: `python3 init_db.py`

### Add a new user (admin flow)
1. Admin logs in at `/admin/login`
2. Navigate to `/admin/users`
3. Enter NetID(s) in bulk add form (space or comma separated)
4. User completes profile on first login at `/profile/setup`

### Flash messages
Use categories: `"success"` (green), `"error"` (red), `"warning"` (yellow), `"info"` (blue)

## Documentation Map

| Document | Purpose |
|----------|---------|
| `README.md` | Performance guide, deployment, troubleshooting |
| `ONBOARDING.md` | This file - quick start for developers |
| `archive/` | Migration scripts, changelogs, deployment guides |

## Development Notes

- **Authentication**: NetID-based for users (no password), password for admins
- **User activation**: Users added by admin are inactive until they complete profile
- **Game deletion**: Users can delete their own games within 15 minutes
- **Tournament games**: Cannot be deleted
- **Cache busting**: VERSION file content appended to static file URLs
- **No test framework**: Manual testing expected

## Production Deployment

**Standard:**
```bash
export FLASK_ENV=production
export FORCE_HTTPS=true
gunicorn -c gunicorn.conf.py app:app
```

**OpenBSD (charterpool.com):**
```bash
# The rc.d/gunicorn_chool script handles production deployment
# Copy to /etc/rc.d/ and enable with: rcctl enable gunicorn_chool
doas rcctl start gunicorn_chool
doas rcctl restart gunicorn_chool
```

Production paths: `/var/www/htdocs/`, database via PostgreSQL

Entry point is `app:app` for Gunicorn/WSGI.

## Maintenance Handoff Checklist

For new maintainers taking over this project:

### Access Requirements
- [ ] SSH access to production server (OpenBSD)
- [ ] GitHub repository access
- [ ] PostgreSQL database access
- [ ] Club administrator contact for user lists

### First-Time Setup
- [ ] Clone repository and set up local dev environment
- [ ] Verify you can run the app locally
- [ ] Obtain production `secrets.txt` from outgoing maintainer
- [ ] Test SSH access to production server

### Semester Workflow
1. **Start of semester**: Bulk add new members via admin panel
2. **Throughout**: Monitor games, tournaments via admin dashboard
3. **End of semester**: Archive graduating users if needed

### Critical Files to Understand
1. `app.py` - All routes and main application logic
2. `models.py` - Database schema and relationships
3. `auth.py` - User/admin authentication flow
4. `elo.py` - Rating calculations
5. `rc.d/gunicorn_chool` - Production service management

### Emergency Procedures
- **App down**: `doas rcctl restart gunicorn_chool`
- **Database issues**: Check PostgreSQL, verify connection string
- **Cache issues**: Restart app (SimpleCache is in-memory)
- **Logs**: Check `/var/log/gunicorn_chool.log`

### Key Contacts
- Club officers: For user list updates and policy changes
