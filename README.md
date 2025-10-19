# Charter Pool

A comprehensive web application for tracking pool games, managing ELO ratings, and organizing tournaments at Princeton Charter Club.

## Overview

Charter Pool provides a complete pool game management system with user authentication, automated ELO rating calculations, tournament brackets, and administrative controls. The application supports both casual game tracking and competitive tournament play with multiple bracket formats.

## Features

### Authentication System

**User Authentication**
- NetID-based login with no password required
- First-time users complete profile with first and last name
- Admins can pre-create user accounts by NetID only
- Users complete their profile on first login
- Persistent sessions lasting 365 days (effectively permanent)
- Automatic session management via Flask-Login
- Archived users cannot log in

**Admin Authentication**
- Separate admin login system with username and password
- Password hashing using Werkzeug security utilities
- Admin accounts managed through admin panel
- Default admin credentials (must be changed in production)

### ELO Rating System

**Core Functionality**
- Standard ELO rating algorithm with K-factor of 32
- Default starting rating of 1200 for all new users
- Automatic rating updates after each game
- Expected score calculation based on rating differential
- Rating changes displayed after game completion
- All games (casual and tournament) affect ELO ratings

**Rating Display**
- Real-time leaderboard with all active users
- User rank calculation and display
- Win/loss records tracked per user
- Win rate percentage calculations
- Rating history preserved through game records

### Game Management

**Game Reporting**
- Users can report games against any other active user
- Winner selection determines ELO changes
- Cannot report games against yourself
- Cannot report games with archived users
- ELO changes calculated and applied immediately
- Game history stored with timestamp and rating change
- Games linked to tournaments when applicable

**Game History**
- Complete game history for each user
- View opponent, winner, ELO change, and timestamp
- Admins can view all games across the platform
- Recent games displayed on user dashboard (10 most recent)
- Full history accessible via dedicated page

### Tournament System

**Tournament Formats**
- Single Elimination: Standard bracket with byes for non-power-of-2 participants
- Double Elimination: Winners and losers brackets with grand finals
- Round Robin: All participants play each other once

**Tournament Lifecycle**

1. **Creation** (Admin Only)
   - Admin creates tournament with name and format
   - Tournament opens for participant signups
   - Status: `open`

2. **Signup Phase**
   - Users sign up with self-rating (1-10 scale)
   - Self-rating used for seeding alongside ELO
   - Multiple tournaments can be open simultaneously
   - Users can join multiple tournaments

3. **Activation** (Admin Only)
   - Requires minimum 2 participants
   - Generates complete bracket structure
   - Seeds participants using composite algorithm
   - Status changes to `active`

4. **Active Phase**
   - Participants report match results
   - Winners advance automatically through bracket
   - Losers eliminated or moved to losers bracket (double elim)
   - ELO ratings updated after each match
   - Game records created for all matches

5. **Completion**
   - Automatically detected when all matches complete
   - Final placements assigned to participants
   - Status changes to `completed`

**Seeding Algorithm**
- Composite score based on self-rating and ELO
- New players (0 games): 100% self-rating, 0% ELO
- Developing players (1-9 games): Linear transition
- Experienced players (10+ games): 10% self-rating, 90% ELO
- Ensures fair brackets for mixed experience levels
- Standard tournament seeding patterns (1v16, 8v9, etc.)

**Bracket Management**
- Automatic advancement for single and double elimination
- Losers bracket population for double elimination
- Grand finals match creation for double elimination
- Round robin matches pre-generated for all pairs
- TBD placeholders for future matches
- Match readiness validation before result reporting

### User Management

**User Profiles**
- NetID (unique identifier)
- First and last name
- Current ELO rating
- Account creation timestamp
- Archived status
- Game history and statistics
- Tournament participation records

**User Administration**
- Add new users by NetID only (user completes profile later)
- Archive users to prevent login and game reporting
- Unarchive previously archived users
- Delete users (only if no games played)
- View active and archived users separately
- User search by NetID, first name, or last name

**User Search**
- Real-time AJAX search functionality
- Search by NetID, first name, or last name
- Minimum 2 characters to search
- Returns up to 10 results with name and ELO
- Used for opponent selection in game reporting

### Admin Panel

**Dashboard**
- Total user count (active and archived)
- Active user count
- Total games played
- Total tournaments created
- Active tournaments count
- Recent game feed (10 most recent)

**User Management**
- View all users (active and archived tabs)
- Add users by NetID
- Archive/unarchive users
- Delete users without game history
- User statistics and ratings

**Admin Account Management**
- View all admin accounts
- Create new admin accounts
- Change admin passwords
- Default admin can change any password
- Regular admins can only change their own password

**Tournament Administration**
- Create tournaments with name and format selection
- Activate tournaments to generate brackets
- View participant lists and seeds
- Monitor tournament progress
- Cannot sign up for or report matches as admin

### User Interface

**Dashboard**
- Personal statistics (ELO, rank, W/L record)
- Recent games (10 most recent)
- Top 10 leaderboard preview
- Open tournaments list
- Active tournaments user is participating in

**Leaderboard**
- Full ranking of all active users
- Sorted by ELO rating (descending)
- Display NetID, full name, and current rating
- Excludes archived users

**Tournament Views**
- List of tournaments (open, active, completed)
- Detailed tournament page with bracket visualization
- Participant list with seeds
- Matches grouped by bracket and round
- Match result reporting interface
- Signup interface for open tournaments

**Navigation**
- Consistent layout across all pages
- User/admin name display in header
- Logout functionality
- Version number in footer
- Responsive design with modern CSS

### Security Features

**Flask-Talisman Integration**
- Content Security Policy (CSP) enforcement
- Inline script and style allowances for functionality
- HTTPS enforcement (configurable)
- Strict Transport Security headers
- 1-year HSTS max age

**Session Security**
- HTTP-only cookies prevent XSS access
- SameSite=Lax protects against CSRF
- Secure cookie flag (configurable for production)
- Session encryption with secret key

**Input Validation**
- NetID format validation and normalization
- Tournament format validation
- Player validation for game reporting
- Winner validation for matches
- Match participant verification

**Access Control**
- Login required for all main functionality
- Admin-only routes protected
- User-specific data access restrictions
- Archived user access prevention
- Match participant verification for reporting

### Database Schema

**users**
- netid (primary key, varchar 50)
- first_name (varchar 100, nullable)
- last_name (varchar 100, nullable)
- elo_rating (integer, default 1200)
- created_at (timestamp)
- archived (boolean, default false)

**admins**
- id (primary key, serial)
- username (varchar 80, unique)
- password_hash (varchar 255)
- created_at (timestamp)

**games**
- id (primary key, serial)
- player1_netid (foreign key to users)
- player2_netid (foreign key to users)
- winner_netid (foreign key to users)
- timestamp (timestamp, default current time)
- tournament_id (foreign key to tournaments, nullable)
- elo_change (integer, winner's rating change)

**tournaments**
- id (primary key, serial)
- name (varchar 200)
- format (varchar 50: single_elim, double_elim, round_robin)
- status (varchar 50: open, active, completed)
- created_at (timestamp)
- created_by_admin_id (foreign key to admins)

**tournament_participants**
- id (primary key, serial)
- tournament_id (foreign key to tournaments)
- user_netid (foreign key to users)
- self_rating (integer 1-10)
- seed (integer, assigned on activation)
- placement (integer, assigned on completion)
- eliminated (boolean, for elimination formats)
- unique constraint on (tournament_id, user_netid)

**tournament_matches**
- id (primary key, serial)
- tournament_id (foreign key to tournaments)
- round_number (integer)
- match_number (integer, position in round)
- bracket (varchar 50: main, winners, losers, grand_finals)
- player1_netid (foreign key to users, nullable for TBD)
- player2_netid (foreign key to users, nullable for TBD)
- winner_netid (foreign key to users, nullable until complete)
- game_id (foreign key to games, nullable until complete)
- completed (boolean, default false)

### Error Handling

**Custom Error Pages**
- 404 Not Found page with navigation
- 500 Internal Server Error page
- Database rollback on server errors
- Flash messages for user feedback
- Validation error messages

**Error Prevention**
- Database constraint validation
- User input sanitization
- Relationship integrity checks
- Transaction rollback on failures
- Match state validation

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/conjfrnk/charter-pool.git
cd charter-pool

# Run the quick setup script
./quickstart.sh
```

The quickstart script will:
1. Create a Python virtual environment
2. Install all dependencies
3. Create the PostgreSQL database
4. Initialize the database schema
5. Create the default admin account

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create PostgreSQL database
createdb charter_pool

# Initialize database
python init_db.py
```

### Running the Application

**Development Mode**
```bash
source venv/bin/activate
python app.py
```
Access at: http://localhost:5000

**Production Mode with Gunicorn**
```bash
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

## Configuration

Edit `config.py` to customize:

**Security Settings**
- `SECRET_KEY`: Session encryption key (reads from secrets.txt or environment)
- `SESSION_COOKIE_SECURE`: Set to True for HTTPS in production
- `DEFAULT_ADMIN_USERNAME`: Default admin username (default: 'admin')
- `DEFAULT_ADMIN_PASSWORD`: Default admin password (default: 'admin')

**Database Settings**
- `DATABASE_URL`: PostgreSQL connection string
- `SQLALCHEMY_TRACK_MODIFICATIONS`: SQLAlchemy event tracking (default: False)

**ELO Settings**
- `ELO_K_FACTOR`: Rating sensitivity (default: 32)
- `ELO_DEFAULT_RATING`: Starting rating for new users (default: 1200)

**Session Settings**
- `PERMANENT_SESSION_LIFETIME`: Session duration (default: 365 days)
- `SESSION_COOKIE_HTTPONLY`: HTTP-only flag (default: True)
- `SESSION_COOKIE_SAMESITE`: SameSite policy (default: 'Lax')

### Environment Variables

```bash
# Secret key (overrides dev default)
export SECRET_KEY="your-secret-key-here"

# Database URL
export DATABASE_URL="postgresql://user:password@localhost/charter_pool"
```

### Secrets File

Create `secrets.txt` in the project root with your secret key:
```
your-secret-key-here
```

Priority: secrets.txt > environment variable > dev default

## Production Deployment

### Server Setup

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx

# Create database
sudo -u postgres createdb charter_pool
sudo -u postgres psql -c "CREATE USER pooluser WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE charter_pool TO pooluser;"

# Clone and setup application
cd /var/www
sudo git clone https://github.com/conjfrnk/charter-pool.git
cd charter-pool
sudo python3 -m venv venv
sudo venv/bin/pip install -r requirements.txt

# Set permissions
sudo chown -R www-data:www-data /var/www/charter-pool
```

### Database Initialization

```bash
cd /var/www/charter-pool
sudo -u www-data venv/bin/python init_db.py
```

### Nginx Configuration

Create `/etc/nginx/sites-available/charter-pool`:

```nginx
server {
    listen 80;
    server_name chool.app www.chool.app;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chool.app www.chool.app;
    
    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/chool.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chool.app/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Application proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Static files
    location /static {
        alias /var/www/charter-pool/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/charter-pool /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d chool.app -d www.chool.app

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

### Systemd Service

Create `/etc/systemd/system/charter-pool.service`:

```ini
[Unit]
Description=Charter Pool Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/charter-pool

# Environment variables
Environment="PATH=/var/www/charter-pool/venv/bin"
Environment="DATABASE_URL=postgresql://pooluser:password@localhost/charter_pool"
Environment="SECRET_KEY=your-production-secret-key-here"

# Gunicorn command
ExecStart=/var/www/charter-pool/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/charter-pool/access.log \
    --error-logfile /var/log/charter-pool/error.log \
    app:app

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
PrivateTmp=true

# Restart policy
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create log directory:
```bash
sudo mkdir -p /var/log/charter-pool
sudo chown www-data:www-data /var/log/charter-pool
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable charter-pool
sudo systemctl start charter-pool
sudo systemctl status charter-pool
```

### Production Checklist

- [ ] Change default admin password immediately
- [ ] Set strong SECRET_KEY in production
- [ ] Configure DATABASE_URL with production credentials
- [ ] Set SESSION_COOKIE_SECURE to True in config.py
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Set up regular database backups
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Review and tighten firewall rules
- [ ] Test backup restoration process
- [ ] Document admin procedures

## API Endpoints

### Public Routes

- `GET /login` - User login page
- `POST /login` - Process user login (NetID)
- `GET /profile/setup` - Profile setup page for new users
- `POST /profile/setup` - Complete profile setup
- `GET /admin/login` - Admin login page
- `POST /admin/login` - Process admin login

### User Routes (Login Required)

**Dashboard and Games**
- `GET /` - Main dashboard with stats and leaderboard
- `GET /games/report` - Game reporting form
- `POST /games/report` - Submit game result
- `GET /games/history` - View game history
- `GET /leaderboard` - Full ELO leaderboard
- `GET /users/search?q=query` - AJAX user search (JSON)

**Tournaments**
- `GET /tournaments` - List all tournaments
- `GET /tournaments/<id>` - Tournament details and bracket
- `POST /tournaments/<id>/signup` - Sign up for tournament
- `POST /tournaments/<id>/matches/<match_id>/report` - Report match result

**Authentication**
- `GET /logout` - Logout current user or admin

### Admin Routes (Admin Login Required)

**Dashboard and Users**
- `GET /admin` - Admin dashboard with statistics
- `GET /admin/users` - User management page
- `POST /admin/users/add` - Add new user by NetID
- `POST /admin/users/<netid>/archive` - Archive user
- `POST /admin/users/<netid>/unarchive` - Unarchive user
- `POST /admin/users/<netid>/delete` - Delete user (if no games)

**Admin Management**
- `GET /admin/admins` - Admin account management
- `POST /admin/admins/add` - Create new admin account
- `POST /admin/admins/<id>/change_password` - Change admin password

**Tournament Management**
- `GET /admin/tournaments/create` - Tournament creation form
- `POST /admin/tournaments/create` - Create tournament
- `POST /admin/tournaments/<id>/activate` - Activate tournament and generate bracket

### Error Pages

- `404` - Not found (custom template)
- `500` - Internal server error (custom template with rollback)

## Project Structure

```
charter-pool/
├── app.py                      # Main Flask application
├── models.py                   # SQLAlchemy database models
├── auth.py                     # Authentication utilities
├── elo.py                      # ELO rating calculations
├── tournament_logic.py         # Tournament bracket generation
├── config.py                   # Configuration settings
├── init_db.py                  # Database initialization script
├── requirements.txt            # Python dependencies
├── VERSION                     # Version number for footer display
├── quickstart.sh              # Quick setup script
├── secrets.txt                # Secret key (gitignored, create manually)
├── static/
│   ├── style.css              # Application styles
│   ├── main.js                # JavaScript for user search and UI
│   └── pcc_logo.png           # Logo image
├── templates/
│   ├── layout.html            # Base template with navigation
│   ├── index.html             # User dashboard
│   ├── login.html             # User login page
│   ├── profile_setup.html     # New user profile setup
│   ├── report_game.html       # Game reporting form
│   ├── game_history.html      # Game history view
│   ├── leaderboard.html       # Full leaderboard
│   ├── tournaments.html       # Tournament list
│   ├── tournament_detail.html # Tournament bracket view
│   ├── admin/
│   │   ├── login.html         # Admin login
│   │   ├── dashboard.html     # Admin dashboard
│   │   ├── users.html         # User management
│   │   ├── admins.html        # Admin management
│   │   └── tournament_create.html  # Tournament creation
│   └── errors/
│       ├── 404.html           # Not found page
│       └── 500.html           # Server error page
└── rc.d/
    └── gunicorn_chool         # FreeBSD rc.d script (if applicable)
```

## Default Credentials

**Admin Login**
- URL: http://localhost:5000/admin/login
- Username: `admin`
- Password: `admin`

**IMPORTANT:** Change the default admin password immediately after first login through the admin panel at `/admin/admins`.

**User Login**
- URL: http://localhost:5000/login
- Enter any NetID to create account or login
- First-time users complete profile with name

## Troubleshooting

### Database Connection Issues

**PostgreSQL not running:**
```bash
# macOS (Homebrew)
brew services start postgresql

# Linux (systemd)
sudo systemctl start postgresql

# Check status
psql --version
```

**Database doesn't exist:**
```bash
# Recreate database
dropdb charter_pool
createdb charter_pool
python init_db.py
```

**Connection refused:**
- Check DATABASE_URL in config.py
- Verify PostgreSQL is listening on correct port
- Check pg_hba.conf for authentication settings

### Application Issues

**Port already in use:**
```bash
# Find process using port 5000
lsof -i :5000
# Or specify different port
python app.py  # Edit app.py to change port
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

**Template not found:**
- Verify templates/ directory structure
- Check file permissions
- Ensure app.py is run from project root

**Static files not loading:**
- Check static/ directory exists
- Verify Nginx configuration for /static location
- Check file permissions

### Admin Issues

**Forgot admin password:**
```bash
# Reset via Python shell
python
>>> from app import app, db
>>> from models import Admin
>>> with app.app_context():
...     admin = Admin.query.filter_by(username='admin').first()
...     admin.set_password('newpassword')
...     db.session.commit()
```

**Cannot create admin:**
- Check that username is unique
- Ensure password is not empty
- Verify database connection

### Tournament Issues

**Cannot activate tournament:**
- Ensure at least 2 participants signed up
- Verify tournament status is 'open'
- Check for database errors in logs

**Matches not advancing:**
- Verify match completion status
- Check winner is one of the match participants
- Review tournament_logic.py for bracket advancement

**Seeding seems incorrect:**
- Check participant self-ratings (1-10 scale)
- Verify user ELO ratings
- Review seeding algorithm in tournament_logic.py

### Production Issues

**502 Bad Gateway:**
- Check Gunicorn service status: `sudo systemctl status charter-pool`
- Review error logs: `sudo tail -f /var/log/charter-pool/error.log`
- Verify bind address matches Nginx proxy_pass

**Static files not loading in production:**
- Check Nginx static file location configuration
- Verify file permissions: `ls -la /var/www/charter-pool/static`
- Test direct file access: `curl localhost/static/style.css`

**Database connection errors in production:**
- Verify DATABASE_URL environment variable
- Check PostgreSQL service: `sudo systemctl status postgresql`
- Test connection: `psql $DATABASE_URL`

## Maintenance

### Database Backups

```bash
# Create backup
pg_dump charter_pool > backup_$(date +%Y%m%d).sql

# Restore backup
psql charter_pool < backup_20241019.sql

# Automated daily backups (add to crontab)
0 2 * * * pg_dump charter_pool > /backups/charter_pool_$(date +\%Y\%m\%d).sql
```

### Updating the Application

```bash
# Pull latest changes
cd /var/www/charter-pool
sudo -u www-data git pull

# Install new dependencies if requirements.txt changed
sudo -u www-data venv/bin/pip install -r requirements.txt

# Run database migrations if needed
sudo -u www-data venv/bin/python init_db.py

# Restart service
sudo systemctl restart charter-pool
```

### Monitoring

**Check application logs:**
```bash
sudo journalctl -u charter-pool -f
```

**Check Nginx logs:**
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Database statistics:**
```bash
psql charter_pool
> SELECT COUNT(*) FROM users;
> SELECT COUNT(*) FROM games;
> SELECT COUNT(*) FROM tournaments;
```

## Development

### Running Tests

```bash
# Test seeding algorithm
python test_seeding.py
```

### Making Changes

1. Create a feature branch
2. Make changes and test locally
3. Update VERSION file if making a release
4. Commit with descriptive message
5. Test in production-like environment
6. Deploy to production

### Database Migrations

The application uses `init_db.py` for initial schema setup. For schema changes:

1. Update models in `models.py`
2. Update `init_db.py` if needed
3. For production, write migration script or use tool like Alembic
4. Test migrations on backup database first
5. Run migrations during maintenance window

## Credits

Created by Connor Frank, Charter House Manager at Princeton University

## License

MIT License - see repository for details
